import '../styles/SearchBar.scss';

export default function Search() {
  return (
    <div className="search-bar">
      <img src="/loop.svg" alt="Loop" width={18} />
      <input
        type="text"
        className="search-input"
        placeholder="Rechercher un quartier, un type de crime..."
        aria-label="Recherche"
      />
    </div>
  );
}