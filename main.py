from location import create_location_graph

def main():
    # Create map-based graph of Lomar
    g = create_location_graph()

    # Print a sample of the data
    print("Number of nodes:", len(g.m_nodes))

    # Plot
    print("Plotting a small part of the map...")
    g.plot()

if __name__ == "__main__":
    main()