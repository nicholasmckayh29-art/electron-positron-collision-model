import matplotlib.pyplot as plt


def plot_mass_histogram(data_set: list[dict], outliers: list[dict]):
    """Show invariant mass distribution with outliers highlighted.
    
    Args:
        data_set: All events from CSV
        outliers: List of outlier events
    """
    all_masses = [record['M'] for record in data_set]
    outlier_masses = [record['M'] for record in outliers]
    
    plt.figure(figsize=(10, 6))
    plt.hist(all_masses, bins=50, alpha=0.7, color='blue', label='All Events')
    plt.hist(outlier_masses, bins=50, alpha=0.8, color='red', label='Outliers')
    plt.xlabel('Invariant Mass M (GeV)')
    plt.ylabel('Frequency')
    plt.title('Invariant Mass Distribution')
    plt.legend()
    plt.show()


def plot_energy_vs_mass(data_set: list[dict], outliers: list[dict]):
    """Scatter plot of total energy vs mass.
    
    Args:
        data_set: All events from CSV
        outliers: List of outlier events
    """
    all_e_total = [record['E1'] + record['E2'] for record in data_set]
    all_masses = [record['M'] for record in data_set]
    
    outlier_e_total = [record['E1'] + record['E2'] for record in outliers]
    outlier_masses = [record['M'] for record in outliers]
    
    plt.figure(figsize=(10, 6))
    plt.scatter(all_masses, all_e_total, alpha=0.5, s=10, c='blue', label='Normal')
    plt.scatter(outlier_masses, outlier_e_total, s=50, c='red', marker='x', label='Outliers')
    plt.xlabel('Invariant Mass M (GeV)')
    plt.ylabel('Total Energy (E1 + E2) (GeV)')
    plt.title('Energy vs Mass')
    plt.legend()
    plt.show()
