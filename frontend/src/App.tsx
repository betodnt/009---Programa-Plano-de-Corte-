import { FormEvent, useEffect, useRef, useState } from 'react';
import { tauriClient } from './lib/tauri';
import type {
  BackendStatus,
  BootstrapData,
  DatabaseCheckResult,
  FinishOperationResult,
  MonitorSnapshot,
  RuntimeConfig,
  StartOperationInput,
  StartOperationResult,
} from './types';

const initialForm: StartOperationInput = {
  pedido: '',
  operador: '',
  maquina: '',
  retalho: 'Chapa Inteira',
  saida: '',
  tipo: 'Avulso',
  owner_id: 'desktop-tauri',
};

export default function App() {
  const [runtime, setRuntime] = useState<RuntimeConfig | null>(null);
  const [status, setStatus] = useState<BackendStatus | null>(null);
  const [dbCheck, setDbCheck] = useState<DatabaseCheckResult | null>(null);
  const [bootstrapData, setBootstrapData] = useState<BootstrapData | null>(null);
  const [monitor, setMonitor] = useState<MonitorSnapshot | null>(null);
  
  const [form, setForm] = useState<StartOperationInput>(initialForm);
  const [availableSaidas, setAvailableSaidas] = useState<string[]>([]);
  
  const [activeOperationId, setActiveOperationId] = useState('');
  const [startResult, setStartResult] = useState<StartOperationResult | null>(null);
  const [feedback, setFeedback] = useState('');
  const [loading, setLoading] = useState(false);
  const [timerString, setTimerString] = useState('00:00:00');
  
  const heartbeatTimer = useRef<number | null>(null);
  const operationTimer = useRef<number | null>(null);
  const startTimeRef = useRef<number | null>(null);

  useEffect(() => {
    void loadInitialState();
    const monitorInterval = setInterval(() => handleRefreshMonitor(), 15000);
    return () => {
      stopHeartbeat();
      stopTimer();
      clearInterval(monitorInterval);
    };
  }, []);

  useEffect(() => {
    if (!activeOperationId) {
      stopHeartbeat();
      stopTimer();
      return;
    }

    void sendHeartbeat();
    heartbeatTimer.current = window.setInterval(() => {
      void sendHeartbeat();
    }, 15000);

    return () => stopHeartbeat();
  }, [activeOperationId]);

  async function loadInitialState() {
    try {
      const dbConfig = await tauriClient.bootstrapDatabase();
      if (!dbConfig.ok) console.warn('Bootstrap falhou', dbConfig.message);
      
      const [runtimeValue, statusValue] = await Promise.all([
        tauriClient.getRuntimeConfig(),
        tauriClient.getBackendStatus(),
      ]);

      setRuntime(runtimeValue);
      setStatus(statusValue);
      
      // Carregar dados de maquinas e operadores
      await handleLoadBootstrapData();
      await handleRefreshMonitor();
    } catch (error) {
      showFeedback(getErrorMessage(error));
    }
  }

  async function handleLoadBootstrapData() {
    try {
      const data = await tauriClient.getBootstrapData();
      setBootstrapData(data);
      setForm((current) => ({
        ...current,
        maquina: current.maquina || data.runtime.machine_name,
        operador: current.operador || data.operators[0]?.name || '',
      }));
    } catch (error) {
      showFeedback(getErrorMessage(error));
    }
  }

  async function handleRefreshMonitor() {
    try {
      const snapshot = await tauriClient.getMonitorSnapshot();
      setMonitor(snapshot);
    } catch (error) {
      console.warn('Monitor erro:', error);
    }
  }

  function showFeedback(msg: string) {
    setFeedback(msg);
    setTimeout(() => setFeedback(''), 5000);
  }

  async function handleSearchCnc() {
    if (!form.pedido || !form.tipo) return;
    setLoading(true);
    try {
      const result = await tauriClient.searchCncFiles({
        pedido: form.pedido,
        tipo: form.tipo,
      });
      // Filter out mapped entries if already locked
      const currentlyLocked = monitor?.active_locks.map((l) => l.saida) || [];
      const available = result.files.filter((f) => !currentlyLocked.includes(f));
      
      setAvailableSaidas(available);
      if (available.length > 0) {
        setForm((prev) => ({ ...prev, saida: available[0] }));
        showFeedback(`Encontrados ${available.length} arquivos.`);
      } else {
        setForm((prev) => ({ ...prev, saida: '' }));
        showFeedback('Nenhuma saída disponivel encontrada.');
      }
    } catch (error) {
      showFeedback(getErrorMessage(error));
    } finally {
      setLoading(false);
    }
  }

  async function handleOpenPdf() {
    if (!form.saida) return;
    try {
      await tauriClient.openPdf({ cnc_filename: form.saida });
      showFeedback('Abrindo PDF...');
    } catch (error) {
      showFeedback(getErrorMessage(error));
    }
  }

  async function handleStartOperation(event?: FormEvent) {
    if (event) event.preventDefault();
    if (!form.saida || !form.operador || !form.maquina) {
      showFeedback('Preencha os campos obrigatorios (Operador, Maquina, Saida).');
      return;
    }
    setLoading(true);
    try {
      const result = await tauriClient.startOperation(form);
      setStartResult(result);
      setActiveOperationId(result.operation_id);
      showFeedback('Corte Iniciado com Sucesso!');
      startTimer();
      await handleRefreshMonitor();
      await handleLoadBootstrapData();
    } catch (error) {
      showFeedback(getErrorMessage(error));
    } finally {
      setLoading(false);
    }
  }

  async function handleFinishOperation() {
    if (!activeOperationId) return;

    if (!window.confirm(`Tem certeza que deseja finalizar a saida '${form.saida}'?`)) {
      return;
    }

    setLoading(true);
    try {
      const result = await tauriClient.finishOperation({
        operation_id: activeOperationId,
      });
      showFeedback(`Operacao finalizada. Tempo decorrido: ${result.elapsed_seconds}s`);
      setActiveOperationId('');
      setForm((prev) => ({ ...prev, saida: '', pedido: '' }));
      setAvailableSaidas([]);
      stopTimer();
      setTimerString('00:00:00');
      await handleRefreshMonitor();
    } catch (error) {
      showFeedback(getErrorMessage(error));
    } finally {
      setLoading(false);
    }
  }

  /* Heartbeat / Timer logic */
  async function sendHeartbeat() {
    if (!activeOperationId) return;
    try {
      const result = await tauriClient.touchOperationLock({ operation_id: activeOperationId });
      if (!result.ok) showFeedback(result.message);
    } catch (error) {
      console.warn('Heartbeat failed', error);
    }
  }

  function stopHeartbeat() {
    if (heartbeatTimer.current !== null) {
      window.clearInterval(heartbeatTimer.current);
      heartbeatTimer.current = null;
    }
  }

  function startTimer() {
    stopTimer();
    startTimeRef.current = Date.now();
    operationTimer.current = window.setInterval(() => {
      if (!startTimeRef.current) return;
      const elapsedMs = Date.now() - startTimeRef.current;
      const totalSeconds = Math.floor(elapsedMs / 1000);
      const h = String(Math.floor(totalSeconds / 3600)).padStart(2, '0');
      const m = String(Math.floor((totalSeconds % 3600) / 60)).padStart(2, '0');
      const s = String(totalSeconds % 60).padStart(2, '0');
      setTimerString(`${h}:${m}:${s}`);
    }, 1000);
  }

  function stopTimer() {
    if (operationTimer.current !== null) {
      window.clearInterval(operationTimer.current);
      operationTimer.current = null;
    }
  }

  const isFormDisabled = loading || activeOperationId !== '';

  return (
    <main className="min-h-screen bg-[#2b2b2b] text-[#d8d8d8] font-sans flex flex-col">
      <header className="bg-[#2f3136] px-6 py-4 flex items-center justify-between border-b border-[#1e1e1e]">
        <div>
          <h1 className="text-2xl font-bold text-white tracking-wide">Controle de Corte e Dobra</h1>
          <p className="text-sm opacity-60">Maquina: <span className="text-[#4a90e2] font-semibold">{runtime?.machine_name || 'Desconhecida'}</span></p>
        </div>
        <div className="flex gap-4">
          <div className="flex flex-col text-right">
             <span className="text-xs uppercase opacity-50">Ambiente</span>
             <strong className="text-sm text-white">{runtime?.app_env || '---'}</strong>
          </div>
          <div className="flex flex-col text-right">
             <span className="text-xs uppercase opacity-50">Banco</span>
             <strong className={`text-sm ${status?.database_connected ? 'text-[#27ae60]' : 'text-[#c0392b]'}`}>
               {status?.database_connected ? 'Conectado' : 'Desconectado'}
             </strong>
          </div>
        </div>
      </header>

      <div className="flex-1 flex flex-col lg:flex-row p-6 gap-6">
        
        {/* Lado Esquerdo - Monitor e Historico */}
        <section className="flex-1 lg:w-1/3 flex flex-col gap-6">
          <div className="bg-[#2f3136] rounded-xl border border-[#3c3f41] p-5 shadow-lg flex-1">
            <h2 className="text-lg font-bold text-white mb-4 border-b border-[#3c3f41] pb-2">Histórico (Em Andamento)</h2>
            <div className="overflow-x-auto">
              <table className="w-full text-left text-sm">
                <thead className="bg-[#3c3f41] text-white">
                  <tr>
                    <th className="p-2 rounded-tl-md">Pedido</th>
                    <th className="p-2">Operador</th>
                    <th className="p-2">Saída</th>
                    <th className="p-2 rounded-tr-md">Tempo</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-[#3c3f41]">
                  {(monitor?.active_operations ?? []).map((op) => (
                    <tr key={op.operation_id} className="hover:bg-[#383a40] transition-colors">
                      <td className="p-2 font-medium">{op.pedido}</td>
                      <td className="p-2">{op.operator_name}</td>
                      <td className="p-2 truncate max-w-[120px]" title={op.saida}>{op.saida}</td>
                      <td className="p-2 text-[#f39c12]">{formatDate(op.started_at)}</td>
                    </tr>
                  ))}
                  {(monitor?.active_operations?.length === 0) && (
                    <tr>
                      <td colSpan={4} className="p-4 text-center opacity-50 italic">Nenhum corte em andamento.</td>
                    </tr>
                  )}
                </tbody>
              </table>
            </div>
          </div>
        </section>

        {/* Lado Direito - Formulario de Iniciar */}
        <section className="flex-[2] flex flex-col gap-6">
          <div className="bg-[#2f3136] rounded-xl border border-[#3c3f41] p-6 shadow-lg">
            <h2 className="text-xl font-bold text-white mb-6 border-b border-[#3c3f41] pb-2">Dados do Corte</h2>
            <form onSubmit={handleStartOperation} className="grid grid-cols-1 md:grid-cols-2 gap-6">
              
              <label className="flex flex-col gap-2">
                <span className="text-sm font-bold opacity-80 uppercase">Operador</span>
                <input
                  type="text"
                  list="operators-list"
                  placeholder="Selecione ou digite..."
                  className="bg-[#3c3f41] text-white p-3 rounded-md border border-transparent focus:border-[#4a90e2] focus:ring-1 focus:ring-[#4a90e2] outline-none transition disabled:opacity-50"
                  value={form.operador}
                  onChange={(e) => setForm({ ...form, operador: e.target.value })}
                  disabled={isFormDisabled}
                  required
                />
                <datalist id="operators-list">
                  {(bootstrapData?.operators ?? []).map((op) => (
                    <option key={op.id} value={op.name} />
                  ))}
                </datalist>
              </label>

              <label className="flex flex-col gap-2">
                <span className="text-sm font-bold opacity-80 uppercase">Tipo</span>
                <select
                  className="bg-[#3c3f41] text-white p-3 rounded-md border border-transparent focus:border-[#4a90e2] focus:ring-1 focus:ring-[#4a90e2] outline-none transition disabled:opacity-50"
                  value={form.tipo}
                  onChange={(e) => setForm({ ...form, tipo: e.target.value })}
                  disabled={isFormDisabled}
                >
                  <option value="Avulso">Avulso</option>
                  <option value="Estoque">Estoque</option>
                  <option value="Pedido">Pedido</option>
                  <option value="Reforma">Reforma</option>
                  <option value="PPD">PPD</option>
                </select>
              </label>

              <label className="flex flex-col gap-2">
                <span className="text-sm font-bold opacity-80 uppercase">Pedido</span>
                <div className="flex gap-2">
                  <input
                    type="text"
                    placeholder="Digite o número e aperte Buscar"
                    className="flex-1 bg-[#3c3f41] text-white p-3 rounded-md border border-transparent focus:border-[#4a90e2] focus:ring-1 focus:ring-[#4a90e2] outline-none transition disabled:opacity-50"
                    value={form.pedido}
                    onChange={(e) => setForm({ ...form, pedido: e.target.value })}
                    onKeyDown={(e) => e.key === 'Enter' && !isFormDisabled && handleSearchCnc()}
                    disabled={isFormDisabled}
                    required
                  />
                  <button
                    type="button"
                    onClick={handleSearchCnc}
                    disabled={isFormDisabled || !form.pedido}
                    className="bg-[#4a90e2] hover:bg-[#3a7bc8] text-white px-4 rounded-md font-bold transition disabled:opacity-50 disabled:bg-[#3c3f41]"
                  >
                    Buscar
                  </button>
                </div>
              </label>

              <label className="flex flex-col gap-2">
                <span className="text-sm font-bold opacity-80 uppercase">Chapa / Retalho</span>
                <select
                  className="bg-[#3c3f41] text-white p-3 rounded-md border border-transparent focus:border-[#4a90e2] focus:ring-1 focus:ring-[#4a90e2] outline-none transition disabled:opacity-50"
                  value={form.retalho}
                  onChange={(e) => setForm({ ...form, retalho: e.target.value })}
                  disabled={isFormDisabled}
                >
                  <option value="Chapa Inteira">Chapa Inteira</option>
                  <option value="Retalho">Retalho</option>
                </select>
              </label>

              <label className="flex flex-col gap-2 md:col-span-2">
                <span className="text-sm font-bold opacity-80 uppercase text-[#f39c12]">Saída CNC a Cortar</span>
                <div className="flex gap-2">
                  <select
                    className="flex-1 bg-[#3c3f41] text-white p-3 rounded-md border border-transparent focus:border-[#f39c12] focus:ring-1 focus:ring-[#f39c12] outline-none transition disabled:opacity-50"
                    value={form.saida}
                    onChange={(e) => setForm({ ...form, saida: e.target.value })}
                    disabled={isFormDisabled || availableSaidas.length === 0}
                    required
                  >
                    <option value="">
                      {availableSaidas.length === 0 ? 'Nenhuma saída encontrada' : 'Selecione uma saída'}
                    </option>
                    {availableSaidas.map((s) => (
                      <option key={s} value={s}>{s}</option>
                    ))}
                  </select>
                  <button
                    type="button"
                    onClick={handleOpenPdf}
                    disabled={!form.saida}
                    className="bg-[#3c3f41] hover:bg-[#4a4c4e] text-white px-5 rounded-md font-bold transition border border-[#1e1e1e] disabled:opacity-40"
                    title="Abrir PDF correspondente"
                  >
                    PDF
                  </button>
                </div>
              </label>
              
              {/* Oculto, mas submete o formulário com Enter se os botoes nao renderizarem bem */}
              <button type="submit" className="hidden" aria-hidden="true" />
            </form>
          </div>

          <div className="bg-[#2f3136] rounded-xl border border-[#3c3f41] shadow-lg p-6 flex flex-col md:flex-row items-center gap-6 justify-between flex-1">
            <div className="flex flex-col items-center justify-center flex-1 min-w-[200px] border-r border-[#3c3f41] pr-6">
              <span className="text-sm font-bold uppercase opacity-60 mb-1">Tempo de Corte</span>
              <div className="text-6xl font-black text-[#f39c12] tracking-widest font-mono drop-shadow-md">
                {timerString}
              </div>
            </div>

            <div className="flex flex-col gap-4 flex-[2] w-full">
              {!activeOperationId ? (
                <button
                  type="button"
                  onClick={(e) => handleStartOperation()}
                  disabled={loading || !form.saida}
                  className="w-full bg-[#27ae60] hover:bg-[#2ecc71] text-white text-2xl font-black py-6 rounded-xl shadow-lg transition-transform transform hover:-translate-y-1 active:translate-y-0 disabled:opacity-40 disabled:hover:translate-y-0"
                >
                  ▶ INICIAR CORTE
                </button>
              ) : (
                <button
                  type="button"
                  onClick={handleFinishOperation}
                  disabled={loading}
                  className="w-full bg-[#c0392b] hover:bg-[#e74c3c] text-white text-2xl font-black py-6 rounded-xl shadow-[0_0_20px_rgba(192,57,43,0.4)] transition-transform transform hover:-translate-y-1 active:translate-y-0 disabled:opacity-40 disabled:hover:translate-y-0 animate-pulse"
                >
                  ■ FINALIZAR CORTE
                </button>
              )}
            </div>
          </div>
        </section>
      </div>

      {/* Alertas Toast */}
      {feedback && (
        <div className="fixed bottom-6 right-6 bg-[#4a90e2] text-white px-6 py-4 rounded-lg shadow-2xl font-bold animate-in fade-in slide-in-from-bottom-4 z-50">
          {feedback}
        </div>
      )}
    </main>
  );
}

function formatDate(value: string) {
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return value;
  return date.toLocaleTimeString('pt-BR', { hour: '2-digit', minute: '2-digit' });
}

function getErrorMessage(error: unknown) {
  if (typeof error === 'string') return error;
  if (error && typeof error === 'object' && 'message' in error) return String(error.message);
  return 'Erro inesperado ao comunicar com o backend.';
}
