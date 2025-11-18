"""
Ponto de entrada principal da aplicação UberUM.
Interface de linha de comando limpa e modular.
"""

from database import load_dataset
from algorithms import DFS, BFS, Dijkstra
from simulation import Simulation
from visualizer import Visualizer


class Menu:
    """Classe para gerenciar o menu da aplicação."""
    
    ALGORITHMS = {
        '1': ('DFS', DFS.find_path, '❌ Rápido mas caminhos longos'),
        '2': ('BFS', BFS.find_path, '🟡 Menor número de arestas'),
        '3': ('Dijkstra', Dijkstra.find_path, '⭐ MENOR TEMPO (Recomendado)'),
    }
    
    @staticmethod
    def print_header():
        """Imprime cabeçalho da aplicação."""
        print("\n" + "="*60)
        print("           🚕 UberUM - Sistema de Simulação 🚕")
        print("="*60)
    
    @staticmethod
    def choose_algorithm():
        """
        Menu para escolha do algoritmo de procura.
        
        Returns:
            tuple: (nome, função) do algoritmo escolhido
        """
        print("\n--- Escolha o Algoritmo de Procura ---")
        
        for key, (name, _, description) in Menu.ALGORITHMS.items():
            print(f"{key} - {name:10} {description}")
        
        choice = input("\nEscolha (1/2/3) [padrão: 3]: ").strip() or '3'
        
        if choice in Menu.ALGORITHMS:
            name, func, _ = Menu.ALGORITHMS[choice]
            print(f"\n✓ Algoritmo selecionado: {name}")
            return name, func
        else:
            print(f"\n⚠ Opção inválida, usando Dijkstra")
            return 'Dijkstra', Dijkstra.find_path
    
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
        
        if mode_choice == '2':
            return {
                'headless': True,
                'show_times': False,
                'show_distances': False
            }
        
        # Modo com visualização
        print("\n--- Opções de Visualização ---")
        print("[S]im - Mostrar tempo de viagem nas arestas")
        print("[N]ão - Mostrar apenas distâncias")
        
        choice = input("\nMostrar tempos? [S/N]: ").strip().lower()
        show_times = choice in ['s', 'sim', 'y', 'yes']
        
        return {
            'headless': False,
            'show_times': show_times,
            'show_distances': not show_times
        }
    
    @staticmethod
    def main_menu():
        """
        Menu principal da aplicação.
        
        Returns:
            str: Opção escolhida ('simulate', 'list', 'exit')
        """
        print("\n--- Menu Principal ---")
        print("1 - Iniciar Simulação")
        print("2 - Listar Veículos")
        print("3 - Sair")
        
        choice = input("\nEscolha (1/2/3): ").strip()
        
        if choice == '1':
            return 'simulate'
        elif choice == '2':
            return 'list'
        elif choice == '3':
            return 'exit'
        else:
            print("⚠ Opção inválida")
            return 'exit'


def run_simulation(database):
    """
    Executa o fluxo completo de simulação.
    
    Args:
        database: Database carregada
    """
    # Escolha do algoritmo
    algo_name, algo_func = Menu.choose_algorithm()
    
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
    
    # Cria simulação com time_step configurado
    simulation = Simulation(database, algo_func, time_step=time_step)
    
    # Informação da simulação
    print(f"\n📊 Informação da Simulação:")
    print(f"   Grafo: {len(database.graph.nodes)} nós, "
          f"{sum(len(e) for e in database.graph.edges.values())} arestas")
    print(f"   Veículos: {len(database.vehicles)}")
    print(f"   Requests: {len(database.requests)}")
    print(f"   Algoritmo: {algo_name}")
    print(f"   Time Step: {time_step} minuto(s) por tick")
    print(f"   Período: 08:00 - 20:00\n")
    
    input("Pressione ENTER para iniciar a simulação...")
    
    # Cria e executa visualizador
    print("\n🎬 Iniciando visualização animada...\n")
    
    visualizer = Visualizer(
        simulation,
        interval=100,  # 100ms = 10 FPS
        **viz_options
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
    print("="*60 + "\n")


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
        
        # Loop principal
        while True:
            action = Menu.main_menu()
            
            if action == 'simulate':
                run_simulation(database)
            elif action == 'list':
                list_vehicles(database)
            elif action == 'exit':
                print("\n👋 Até logo!\n")
                break
    
    except KeyboardInterrupt:
        print("\n\n⚠ Simulação interrompida pelo utilizador\n")
    except Exception as e:
        print(f"\n❌ Erro: {e}\n")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
