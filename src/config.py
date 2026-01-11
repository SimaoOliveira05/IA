"""
Configurações globais do sistema UberUM.
Centraliza todas as constantes e parâmetros configuráveis.
"""

# =============================================================================
# SIMULAÇÃO
# =============================================================================
SIMULATION_START_TIME = 8 * 60   # 08:00 em minutos
SIMULATION_END_TIME = 20 * 60    # 20:00 em minutos
DEFAULT_TIME_STEP = 1            # Minutos por tick
EVENT_UPDATE_INTERVAL = 30       # Intervalo em minutos para atualizar eventos

# =============================================================================
# GRAFO E ESCALA
# =============================================================================
SCALE_FACTOR = 15                # Fator de escala para simular área maior
DEFAULT_EDGE_SPEED_KMH = 50      # Velocidade padrão das arestas em km/h

# =============================================================================
# PREÇOS DE ENERGIA
# =============================================================================
PRECO_BATERIA = 0.15             # €/kWh (preço da eletricidade)
PRECO_COMBUSTIVEL = 1.80         # €/litro (preço do combustível)

# =============================================================================
# ABASTECIMENTO
# =============================================================================
REFUEL_TIME = 5.0                # Tempo de abastecimento de combustível (minutos)
RECHARGE_TIME = 30.0             # Tempo de recarga de bateria (minutos)
SAFETY_MARGIN = 0.15             # Margem de segurança para abastecimento (15%)

# =============================================================================
# EMISSÕES DE CO₂
# =============================================================================
EMISSIONS_COMBUSTION_G_PER_KM = 120.0   # g CO₂/km para veículos a combustão
EMISSIONS_HYBRID_G_PER_KM = 90.0        # g CO₂/km para híbridos (em modo combustão)
CO2_KG_PER_LITER_GASOLINE = 2.3         # kg CO₂ por litro de gasolina

# =============================================================================
# CONVERSÕES PARA HEURÍSTICAS
# =============================================================================
EURO_TO_METERS = 200.0           # 1€ equivale a 200m de "distância equivalente"
CO2_TO_METERS = 6                # Conversão de emissões para distância equivalente

# =============================================================================
# FUNÇÃO DE CUSTO (PESOS)
# =============================================================================
PESO_TEMPO = 0.35                # Peso do tempo de resposta
PESO_CUSTO = 0.50                # Peso do custo operacional
PESO_AMBIENTE = 0.15             # Peso da sustentabilidade ambiental

# =============================================================================
# NORMALIZAÇÃO (BASE PARA 1KM)
# =============================================================================
CUSTO_BASE_EUR = 0.15            # ~0.15€ por km (média entre elétrico e combustão)
EMISSOES_BASE_G = 60.0           # ~60g CO₂/km (média considerando mix de veículos)

# =============================================================================
# HEURÍSTICAS
# =============================================================================
DEFAULT_SPEED_KMH = 50.0         # Velocidade média padrão
COST_PER_KM = 0.50               # Custo por km (fallback)
COST_PER_MIN = 0.20              # Custo por minuto (fallback)

# =============================================================================
# PENALIZAÇÕES DE TRÂNSITO (HEURÍSTICA TRAFFIC_AVOIDANCE)
# =============================================================================
TRAFFIC_PENALTIES = {
    'clear': 1.0,
    'light': 1.3,
    'moderate': 1.8,
    'heavy': 2.5,
    'congested': 4.0,
}
TRAFFIC_PROPAGATION_FACTOR = 1.5  # Fator de propagação do trânsito
