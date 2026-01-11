"""
Ponto de entrada principal da aplicação UberUM.
Interface de linha de comando limpa e modular.
"""

from database import load_dataset
from algorithms import ALGORITHMS
from simulation import Simulation
from visualizer import Visualizer


class Menu:
    """Classe para gerenciar o menu da aplicação."""
    
    # Dicionário de algoritmos: (nome, função, é_informado)
    # Import movido para fora da classe para melhor prática
    ALGORITHMS = {
        '1': ('A*', ALGORITHMS['a_star'], True),
        '2': ('Greedy', ALGORITHMS['greedy'], True),
        '3': ('BFS', ALGORITHMS['bfs'], False),
        '4': ('DFS', ALGORITHMS['dfs'], False),
        '5': ('Uniform Cost', ALGORITHMS['uniform_cost'], False),
    }
    
    @staticmethod
    def print_header():
        """Imprime cabeçalho da aplicação."""
        print("\n" + "="*60)
        print("           🚕 UberUM - Sistema de Simulação 🚕")
        print("="*60)
    
    @staticmethod
    def choose_heuristic():
        """
        Menu para escolha da heurística (apenas para algoritmos informados).
        
        Returns:
            str: Nome da heurística escolhida
        """
        from algorithms.informed.heuristics import HEURISTICS
        
        print("\n--- Escolha a Heurística ---")
        heuristic_keys = list(HEURISTICS.keys())
        for i, (key, description) in enumerate(HEURISTICS.items(), 1):
            print(f"{i} - {description}")
        
        choice = input(f"\nEscolha (1-{len(HEURISTICS)}) [padrão: 1]: ").strip() or '1'
        
        try:
            idx = int(choice) - 1
            if 0 <= idx < len(heuristic_keys):
                heuristic = heuristic_keys[idx]
                print(f"\n✓ Heurística selecionada: {HEURISTICS[heuristic]}")
                return heuristic
        except ValueError:
            pass
        
        print(f"\n⚠ Opção inválida, usando Distância Euclidiana")
        return 'distance'
    
    @staticmethod
    def choose_algorithm():
        """
        Menu para escolha do algoritmo de procura.
        
        Returns:
            tuple: (nome, função, heurística ou None) do algoritmo escolhido
        """
        print("\n--- Escolha o Algoritmo de Procura ---")
        
        for key, (name, _, is_informed) in Menu.ALGORITHMS.items():
            marker = "🎯" if is_informed else "🔍"
            print(f"{key} - {marker} {name}")
        
        choice = input("\nEscolha (1-5) [padrão: 1]: ").strip() or '1'
        
        if choice in Menu.ALGORITHMS:
            name, func, is_informed = Menu.ALGORITHMS[choice]
            print(f"\n✓ Algoritmo selecionado: {name}")
            
            # Se é algoritmo informado, pede heurística
            heuristic = None
            if is_informed:
                heuristic = Menu.choose_heuristic()
            
            return name, func, heuristic
        else:
            print(f"\n⚠ Opção inválida, usando A*")
            heuristic = Menu.choose_heuristic()
            return 'A*', ALGORITHMS['a_star'], heuristic
    
    @staticmethod
    def choose_visualization():
        """
        Menu para opções de visualização.
        
        Returns:
            dict: Configurações de visualização
        """
        print("\n--- Modo de Execução ---")
        print("1 - Com visualização (mais lento, interativo)")
        print("2 - Sem visualização (RÁPIDO, apenas estatísticas)")
        
        mode_choice = input("\nEscolha [1/2] (padrão: 1): ").strip() or '1'
        
        return {'headless': mode_choice == '2'}
    
def run_simulation(database):
    """
    Executa o fluxo completo de simulação.
    
    Args:
        database: Database carregada
    """
    # Escolha do algoritmo e heurística
    algo_name, algo_func, heuristic = Menu.choose_algorithm()
    
    # Opções de visualização
    viz_options = Menu.choose_visualization()
    
    # Pergunta sobre velocidade da simulação
    print("\n--- Velocidade da Simulação ---")
    print("Quantos minutos devem passar a cada tick?")
    print("[1] 1 minuto (padrão - mais lento)")
    print("[2] 2 minutos")
    print("[5] 5 minutos (mais rápido)")
    
    time_step_input = input("\nEscolha [1/2/5]: ").strip()
    time_step = int(time_step_input) if time_step_input in ['1', '2', '5'] else 1
    
    # Cria simulação com time_step e heurística configurados
    simulation = Simulation(database, algo_func, time_step=time_step, heuristic=heuristic)
    
    # Informação da simulação
    print(f"\n📊 Informação da Simulação:")
    print(f"   Grafo: {len(database.graph.nodes)} nós, "
          f"{sum(len(e) for e in database.graph.edges.values())} arestas")
    print(f"   Veículos: {len(database.vehicles)}")
    print(f"   Requests: {len(database.requests)}")
    print(f"   Algoritmo: {algo_name}")
    if heuristic:
        from algorithms.informed.heuristics import HEURISTICS
        print(f"   Heurística: {HEURISTICS.get(heuristic, heuristic)}")
    print(f"   Time Step: {time_step} minuto(s) por tick")
    print(f"   Período: 08:00 - 20:00\n")
    
    input("Pressione ENTER para iniciar a simulação...")
    
    # Modo headless (sem visualização)
    if viz_options.get('headless', False):
        print("\n⚡ Executando em modo rápido (sem visualização)...\n")
        
        # Executa simulação completa
        while not simulation.is_finished():
            simulation.step()
        
        print("✓ Simulação concluída!\n")
    
    # Modo com visualização
    else:
        print("\n🎬 Iniciando visualização animada...\n")
        
        visualizer = Visualizer(
            simulation,
            interval=100  # 100ms = 10 FPS
        )
        
        visualizer.run()
    
    # Mostra estatísticas finais
    print("\n" + "="*60)
    print("           📊 ESTATÍSTICAS FINAIS")
    print("="*60)
    stats = simulation.stats
    print(f"Requests completados: {stats['requests_completed']}/{len(database.requests)}")
    print(f"Requests pendentes:   {stats['requests_pending']}")
    print(f"Distância total:      {stats['total_distance']:.2f} metros")
    print(f"Tempo total:          {stats['total_time']:.2f} minutos")
    print(f"Custo combustível:    {stats['total_fuel_cost']:.2f} €")
    
    # Estatísticas de tempo de procura do algoritmo
    print("\n" + "-"*60)
    print("           ⏱️  DESEMPENHO DO ALGORITMO")
    print("-"*60)
    print(f"Número de procuras:   {stats.get('search_count', 0)}")
    print(f"Tempo total:          {stats.get('search_time_total_ms', 0):.2f} ms")
    print(f"Tempo médio:          {stats.get('search_time_avg_ms', 0):.4f} ms")
    print(f"Tempo mínimo:         {stats.get('search_time_min_ms', 0):.4f} ms")
    print(f"Tempo máximo:         {stats.get('search_time_max_ms', 0):.4f} ms")
    
    # Estatísticas ambientais
    print("\n" + "-"*60)
    print("           🌱 IMPACTO AMBIENTAL")
    print("-"*60)
    
    total_emissions = 0.0
    total_distance = 0.0
    
    for vehicle in simulation.vehicles:
        impact = vehicle.get_environmental_impact()
        total_emissions += impact['total_emissions_g']
        total_distance += impact['total_distance_km']
        
        vehicle_type_name = type(vehicle.vehicle_type).__name__
        emoji = "⚡" if vehicle_type_name == "Eletric" else "🔥" if vehicle_type_name == "Combustion" else "🔋"
        
        print(f"{emoji} {vehicle.name} ({vehicle_type_name}):")
        print(f"   Distância: {impact['total_distance_km']:.2f} km")
        print(f"   Emissões: {impact['total_emissions_g']:.1f}g CO₂")
        if impact['total_distance_km'] > 0:
            print(f"   Média: {impact['average_emissions_per_km']:.1f}g CO₂/km")
    
    print(f"\n🌍 TOTAL DA FROTA:")
    print(f"   Distância: {total_distance:.2f} km")
    print(f"   Emissões: {total_emissions:.1f}g CO₂ ({total_emissions/1000:.3f} kg)")
    if total_distance > 0:
        print(f"   Média: {total_emissions/total_distance:.1f}g CO₂/km")
    
    # Função de Custo Total com pesos iguais
    print("\n" + "-"*60)
    print("           💰 FUNÇÃO DE CUSTO TOTAL")
    print("-"*60)
    print("C = α·F + β·T + ε·R + θ·D + δ·A")
    print("(Pesos iguais: α = β = ε = θ = δ = 1.0)")
    

    # Componentes do custo (normalizados)
    F_norm = stats.get('total_fuel_cost', 0.0)  # Já em euros
    T_norm = stats['total_time'] / 60.0  # Converte minutos para horas
    R_norm = stats['requests_pending']  # Número de requests
    D_norm = stats['total_distance'] / 1000.0  # Converte metros para km
    A_norm = total_emissions / 1000.0  # Converte gramas para kg
    
    # Pesos iguais
    alpha = beta = epsilon = theta = delta = 1.0
    
    # Calcula custo total
    C = alpha * F_norm + beta * T_norm + epsilon * R_norm + theta * D_norm + delta * A_norm
    
    print(f"\nComponentes (normalizados):")
    print(f"  F (combustível)     = {F_norm:.2f} €")
    print(f"  T (tempo)           = {T_norm:.2f} horas")
    print(f"  R (não atendidos)   = {R_norm}")
    print(f"  D (distância)       = {D_norm:.2f} km")
    print(f"  A (emissões)        = {A_norm:.3f} kg CO₂")
    print(f"\n💰 CUSTO TOTAL: C = {C:.2f}")
    
    print("="*60 + "\n")
    
    # Exporta resultados para ficheiro
    export_results_to_file(
        algo_name=algo_name,
        heuristic=heuristic,
        stats=stats,
        total_emissions=total_emissions,
        total_distance=total_distance,
        C=C,
        F_norm=F_norm,
        T_norm=T_norm,
        R_norm=R_norm,
        D_norm=D_norm,
        A_norm=A_norm
    )


def export_results_to_file(algo_name, heuristic, stats, total_emissions, total_distance,
                           C, F_norm, T_norm, R_norm, D_norm, A_norm,
                           filename="../data/resultados_simulacao.txt"):
    """
    Exporta os resultados da simulação para um ficheiro de texto.
    Faz append para permitir múltiplas simulações no mesmo ficheiro.
    
    Args:
        algo_name: Nome do algoritmo usado
        heuristic: Heurística usada (ou None)
        stats: Dicionário com estatísticas da simulação
        total_emissions: Total de emissões em gramas
        total_distance: Distância total em km
        C: Custo total calculado
        F_norm, T_norm, R_norm, D_norm, A_norm: Componentes normalizados
        filename: Nome do ficheiro de saída
    """
    from datetime import datetime
    from algorithms.informed.heuristics import HEURISTICS
    
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    heuristic_name = HEURISTICS.get(heuristic, "N/A") if heuristic else "N/A"
    
    with open(filename, "a", encoding="utf-8") as f:
        f.write(f"Algoritmo: {algo_name}\n")
        f.write(f"Heurística: {heuristic_name}\n")
        f.write("-"*70 + "\n")
        f.write("ESTATÍSTICAS GERAIS:\n")
        f.write(f"  Requests completados: {stats['requests_completed']}\n")
        f.write(f"  Distância total: {stats['total_distance']:.2f} metros\n")
        f.write(f"  Tempo total: {stats['total_time']:.2f} minutos\n")
        f.write(f"  Custo combustível: {stats['total_fuel_cost']:.2f} €\n")
        f.write(f"  Emissões totais: {total_emissions:.1f} g CO₂ ({total_emissions/1000:.3f} kg)\n")

        f.write("-"*70 + "\n")
        f.write("DESEMPENHO DO ALGORITMO:\n")
        f.write(f"  Número de procuras: {stats.get('search_count', 0)}\n")
        f.write(f"  Tempo total: {stats.get('search_time_total_ms', 0):.2f} ms\n")
        f.write(f"  Tempo médio: {stats.get('search_time_avg_ms', 0):.4f} ms\n")
        f.write(f"  Tempo mínimo: {stats.get('search_time_min_ms', 0):.4f} ms\n")
        f.write(f"  Tempo máximo: {stats.get('search_time_max_ms', 0):.4f} ms\n")
        f.write("-"*70 + "\n")
    print(f"📁 Resultados exportados para: {filename}")


def list_vehicles(database):
    """Lista todos os veículos."""
    database.list_vehicles()


def main():
    """Função principal da aplicação."""
    try:
        Menu.print_header()
        
        # Carrega dados
        print("\n📂 Carregando dados...")
        database = load_dataset("../data/dataset.json")
        print("✓ Dados carregados com sucesso!")

        run_simulation(database)

    except KeyboardInterrupt:
        print("\n\n⚠ Simulação interrompida pelo utilizador\n")
    except Exception as e:
        print(f"\n❌ Erro: {e}\n")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
