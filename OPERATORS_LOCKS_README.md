# Histórico de Operadores + Bloqueio de Conflitos

## O que foi implementado?

### 1. **Histórico Persistente de Operadores** 📝

Agora os operadores anteriormente usados são salvos automaticamente em um arquivo `recent_operators.json`. Quando você abre a aplicação novamente, os últimos operadores aparecem no dropdown para seleção rápida.

**Funcionalidade:**

- Salva automaticamente cada operador usado
- Mantém último 10 operadores
- Acessa XMLs recentes se houver menos de 3 operadores no histórico
- Operador mais recentemente usado aparece em primeiro lugar

### 2. **Bloqueio de Máquina + Plano de Corte** 🔒

Quando você inicia uma operação de corte em uma máquina com um plano específico, nenhum outro usuário pode escolher a mesma combinação. Isso evita conflitos onde dois usuários tentariam trabalhar com a mesma máquina e plano.

**Como funciona:**

- Quando você clica em "INICIAR": a combinação `máquina + plano_de_corte` é marcada como "bloqueada"
- Outro usuário vendo aquele plano no dropdown verá como **indisponível**
- Quando você finaliza ou cancela: o bloqueio é liberado automaticamente
- Bloqueios expiram automaticamente após 1 hora (em caso de crash da app)

**Visualização:**

```
Resultado de busca: [saida001.cnc, saida002.cnc, saida003.cnc]
Usuário A escolheu "saida002.cnc" e clicou "INICIAR"

Instância de Usuário B vê:
[saida001.cnc, saida003.cnc]  ← saida002 desapareceu do dropdown!
```

## Arquivos Criados/Modificados

### Novos Arquivos:

- **`core/operators.py`** - Gerencia histórico persistente de operadores
- **`core/locks.py`** - Gerencia bloqueios de máquina + plano de corte
- **`recent_operators.json`** - Arquivo de dados (criado automaticamente)
- **`active_locks.json`** - Arquivo de controle de locks (criado automaticamente)

### Modificados:

- **`gui/app_window.py`** - Integra OperatorsManager e LocksManager
- **`gui/form_panel.py`** - Filtra saídas bloqueadas

## Como Usar?

### Para Usuários:

1. **Primeira execução:** Funciona normalmente
2. **Segundas em diante:** Seu nome aparece no dropdown de OPERADOR automáticamente
3. **Bloqueios automáticos:** Você não vê planos que outro usuário está usando na mesma máquina

### Para Desenvolvedores:

#### Adicionar operador ao histórico:

```python
from core.operators import OperatorsManager

OperatorsManager.add_operator("José da Silva")
```

#### Verificar/Gerenciar locks:

```python
from core.locks import LocksManager

# Adquirir lock
LocksManager.acquire_lock("Bodor1 (12K)", "saida001.cnc")

# Verificar se está bloqueado
if LocksManager.is_locked("Bodor1 (12K)", "saida001.cnc"):
    print("Bloqueado por outro usuário")

# Liberar lock
LocksManager.release_lock("Bodor1 (12K)", "saida001.cnc")

# Ver quais saídas estão bloqueadas
locked = LocksManager.get_locked_saidas("Bodor1 (12K)")
```

## Comportamento Técnico

### OperatorsManager

- Persiste em JSON (facilita backup/compartilhamento)
- Limite de 10 operadores históricos
- Movidos para frente quando reutilizados (LRU - Least Recently Used)

### LocksManager

- Cada lock é: `máquina|plano`
- Locksum arquivo JSON compartilhado entre instâncias
- PID (Process ID) garante que apenas o processo que criou o lock vê como "seu"
- Timeout automático: 1 hora (limpar locks de apps travadas)

## Arquivos de Dados

```
recent_operators.json
{
  "operators": [
    "João Silva",
    "Maria Santos",
    "Pedro Costa"
  ]
}

active_locks.json
{
  "Bodor1 (12K)|saida001.cnc": {
    "maquina": "Bodor1 (12K)",
    "saida": "saida001.cnc",
    "pid": 12345,      ← Process ID da instância
    "timestamp": 1773860830.5  ← Quando foi criado
  }
}
```

## Testes

Execute os scripts de teste para validar:

```bash
# Teste básico de operadores e locks
python test_operators_locks.py

# Teste com múltiplas instâncias simuladas
python test_multi_instance.py
```

## Possíveis Melhorias Futuras

- [ ] Visualizar quem está usando qual máquina (modo "network")
- [ ] Timeout configurável via `config.ini`
- [ ] Persistência em banco de dados (em vez de JSON)
- [ ] Limite de tempo de lock personalizável por máquina
- [ ] Notificação quando um lock é liberado
