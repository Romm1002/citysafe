import { useState, useEffect } from 'react';
import '../styles/SearchBar.scss';

export default function SearchBar({ onSearch, value }) {
  const [term, setTerm] = useState('');

  useEffect(() => {
    setTerm(value);
  }, [value]);

  const handleSubmit = e => {
    e.preventDefault();
    const name = term.trim();
    if (name) onSearch(name);
  };

  return (
    <form className="search-bar" onSubmit={handleSubmit}>
      <input
        type="text"
        value={term}
        onChange={e => setTerm(e.target.value)}
        placeholder="Rechercher un quartier…"
        className="search-input"
      />
      <button type="submit" className="search-button">🔍</button>
    </form>
  );
}
