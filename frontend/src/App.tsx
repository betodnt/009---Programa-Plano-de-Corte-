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
  const [bootstrapData, setBootstrapData] = useState<BootstrapData | null>(null);
  const [monitor, setMonitor] = useState<MonitorSnapshot | null>(null);
  
  const [form, setForm] = useState<StartOperationInput>(initialForm);
  const [availableSaidas, setAvailableSaidas] = useState<string[]>([]);
  
  const [activeOperationId, setActiveOperationId] = useState('');
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

  const inputClass = "w-full bg-[#3c3f41] text-[#ffffff] px-[6px] py-[6px] border border-[#3c3f41] focus:border-[#4a90e2] outline-none disabled:bg-[#3c3f41] disabled:opacity-80";

  return (
    <div className="h-screen w-screen bg-[#2b2b2b] p-3 flex overflow-hidden font-['Segoe_UI'] text-[14px]">
      
      {/* Historico Card (Left Panel - 30%) */}
      <div className="w-[30%] bg-[#2f3136] flex flex-col mr-3.5">
        <div className="px-3 py-3 relative z-10">
          <span className="text-[#d8d8d8] font-bold text-[13px] tracking-wide">HISTORICO</span>
        </div>
        <div className="flex-1 overflow-x-auto overflow-y-auto px-3 pb-3 relative">
          <table className="w-full text-left text-[13px] border-none border-collapse text-[#ffffff]">
            <thead className="bg-[#3c3f41] sticky top-0 z-20 shadow-sm font-bold">
              <tr>
                <th className="px-1.5 py-1 font-bold text-center w-[27%]">PEDIDO</th>
                <th className="px-1.5 py-1 font-bold w-[51%]">SAIDA</th>
                <th className="px-1.5 py-1 font-bold text-center w-[22%]">TEMPO</th>
              </tr>
            </thead>
            <tbody className="bg-[#2b2b2b]">
              {(monitor?.active_operations ?? []).map((op) => (
                <tr key={op.operation_id} className="h-[28px] hover:bg-[#4a90e2] transition-colors cursor-default">
                  <td className="px-1.5 text-center truncate max-w-[80px]">{op.pedido}</td>
                  <td className="px-1.5 truncate max-w-[140px]" title={op.saida}>{op.saida}</td>
                  <td className="px-1.5 text-center">{formatDate(op.started_at)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* Right Container - 70% */}
      <div className="flex-1 flex flex-col">
        
        {/* Form Card */}
        <div className="bg-[#2f3136] flex-1 mb-3.5 flex flex-col justify-center">
          <form onSubmit={handleStartOperation} className="px-2.5 py-3 flex flex-col gap-4">
            
            <div className="grid grid-cols-2 gap-x-5 max-w-[800px]">
              {/* Row 1 */}
              <div className="col-span-1 flex flex-col justify-end pb-4">
                <span className="text-[#d8d8d8] font-bold text-[13px] tracking-wide mb-1 px-0.5">OPERADOR</span>
                <input
                  type="text"
                  list="operators-list"
                  className={inputClass}
                  value={form.operador}
                  onChange={(e) => setForm({ ...form, operador: e.target.value })}
                  disabled={isFormDisabled}
                />
                <datalist id="operators-list">
                  {(bootstrapData?.operators ?? []).map((op) => (
                    <option key={op.id} value={op.name} />
                  ))}
                </datalist>
              </div>

              <div className="col-span-1 flex items-center justify-between px-2.5 pb-4">
                <span className="text-[#ffffff] text-[28px] font-bold leading-none">{runtime?.machine_name || 'Desconhecido'}</span>
                <button
                  type="button"
                  onClick={() => alert('Settings: Replicar funcionalidade (Em breve)')}
                  className="bg-[#2b2b2b] hover:bg-[#3c3f41] active:bg-[#4e5254] text-[#ffffff] text-[19px] py-1 px-3"
                  title="Configuracoes"
                >
                  ⚙
                </button>
              </div>

              {/* Row 2 */}
              <div className="col-span-1 pb-4">
                <span className="text-[#d8d8d8] font-bold text-[13px] tracking-wide mb-1 px-0.5 block">TIPO</span>
                <select
                  className={inputClass}
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
              </div>

              <div className="col-span-1 pb-4">
                <span className="text-[#d8d8d8] font-bold text-[13px] tracking-wide mb-1 px-0.5 block">PEDIDO</span>
                <input
                  type="text"
                  className={inputClass}
                  value={form.pedido}
                  onChange={(e) => setForm({ ...form, pedido: e.target.value })}
                  onKeyDown={(e) => e.key === 'Enter' && !isFormDisabled && handleSearchCnc()}
                  disabled={isFormDisabled}
                />
              </div>

              {/* Row 3 */}
              <div className="col-span-1 pb-4">
                <span className="text-[#d8d8d8] font-bold text-[13px] tracking-wide mb-1 px-0.5 block">CHAPA / RETALHO</span>
                <select
                  className={inputClass}
                  value={form.retalho}
                  onChange={(e) => setForm({ ...form, retalho: e.target.value })}
                  disabled={isFormDisabled}
                >
                  <option value="Chapa Inteira">Chapa Inteira</option>
                  <option value="Retalho">Retalho</option>
                </select>
              </div>

              <div className="col-span-1 pb-4">
                <span className="text-[#d8d8d8] font-bold text-[13px] tracking-wide mb-1 px-0.5 block">SAIDA CNC A CORTAR</span>
                <div className="flex bg-[#2b2b2b]">
                  <select
                    className={inputClass + " flex-1 min-w-0 pr-1"}
                    value={form.saida}
                    onChange={(e) => setForm({ ...form, saida: e.target.value })}
                    disabled={isFormDisabled || availableSaidas.length === 0}
                  >
                    {availableSaidas.length === 0 ? (
                       <option value=""></option>
                    ) : (
                       availableSaidas.map((s) => <option key={s} value={s}>{s}</option>)
                    )}
                  </select>
                  <button
                    type="button"
                    onClick={handleOpenPdf}
                    disabled={!form.saida}
                    className="bg-[#3c3f41] hover:bg-[#4e5254] text-[#ffffff] font-bold text-[12px] px-3 ml-2 shrink-0 disabled:opacity-80 active:bg-[#555555]"
                  >
                    PDF
                  </button>
                </div>
              </div>
            </div>
            {/* Oculto mas suporta submeter com o Enter */}
            <button type="submit" className="hidden" aria-hidden="true" />
          </form>
        </div>

        {/* Action Card */}
        <div className="bg-[#2f3136] py-3 flex flex-col justify-end shrink-0">
          <div className="flex justify-between items-center mb-3 px-3">
             <span className={`font-bold text-[13px] ${status?.database_connected ? 'text-[#7ed957]' : 'text-[#f39c12]'}`}>
                {status?.database_connected ? 'Rede OK' : 'Verificando rede...'}
             </span>
             <span className="text-[#f39c12] font-bold text-[36px] tracking-wide leading-none">{timerString}</span>
          </div>

          <div className="flex px-3 pb-3 justify-end gap-3 h-[60px]">
             <button
               type="button"
               onClick={() => handleStartOperation()}
               disabled={loading || activeOperationId !== ''}
               className="bg-[#27ae60] hover:bg-[#2ecc71] active:bg-[#4e5254] font-bold text-[16px] w-[140px] tracking-wide text-[#ffffff] disabled:opacity-40"
             >
               INICIAR
             </button>
             <button
               type="button"
               onClick={handleFinishOperation}
               disabled={activeOperationId === '' || loading}
               className="bg-[#c0392b] hover:bg-[#e74c3c] active:bg-[#4e5254] font-bold text-[16px] w-[140px] tracking-wide text-[#ffffff] disabled:opacity-40"
             >
               FINALIZAR
             </button>
          </div>
        </div>
      </div>

      {feedback && (
        <div className="fixed top-1/2 left-1/2 transform -translate-x-1/2 -translate-y-1/2 bg-[#34495e] text-white px-10 py-6 rounded-none font-bold text-[28px] shadow-2xl z-50 text-center font-['Segoe_UI'] min-w-[300px]">
          {feedback}
        </div>
      )}
    </div>
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
