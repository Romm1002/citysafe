import '../styles/Filters.scss';

export default function Filters() {
  return (
    <div className="filters">
      <select className="filter-select" aria-label="Filtrer par type de crime">
        <option value="">Tous les types</option>
        <option value="theft">Vol</option>
        <option value="assault">Agression</option>
        <option value="drug">Drogue</option>
      </select>

      <input
        type="date"
        className="filter-date"
        aria-label="Filtrer par date"
      />

      <select className="filter-select" aria-label="Filtrer par arrondissement">
        <option value="">Tous les arrondissements</option>
        <option value="Manhattan">Manhattan</option>
        <option value="Brooklyn">Brooklyn</option>
        <option value="Queens">Queens</option>
        <option value="Bronx">Bronx</option>
        <option value="Staten Island">Staten Island</option>
      </select>
    </div>
  );
}
