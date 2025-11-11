from database import load_dataset

def main():
    print("\n--- UberUM: Visualização de Grafo Urbano ---\n")
    db = load_dataset("../data/dataset.json")

    print(f"\nGrafo criado com {len(db.graph.nodes)} nós e {sum(len(e) for e in db.graph.edges.values())} arestas.")
    print("\nOpções de visualização:")
    print("  [S]im  - Mostrar tempo estimado de viagem em cada aresta")
    print("  [N]ão  - Mostrar apenas as distâncias das arestas")
    resposta = input("\nPretende ver o tempo estimado de viagem em cada aresta? [S/N]: ")
    resposta = resposta.strip().lower()
    if resposta in ['s', 'sim', 'y', 'yes']:
        print("\nA desenhar o mapa com tempos de viagem (em minutos)...\n")
        db.graph.plot(show_times=True, show_distances=False)
    else:
        print("\nA desenhar o mapa com distâncias (em metros)...\n")
        db.graph.plot(show_times=False, show_distances=True)
    print("\n--- Fim da visualização ---\n")

    db.list_vehicles()

if __name__ == "__main__":
    main()