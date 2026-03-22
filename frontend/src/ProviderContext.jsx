import { createContext, useContext, useState } from 'react';

const ProviderContext = createContext(null);

const STORAGE_KEY = 'cm_provider';

function loadStored() {
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    return raw ? JSON.parse(raw) : null;
  } catch {
    return null;
  }
}

export function ProviderProvider({ children }) {
  const [provider, setProviderState] = useState(loadStored);

  function setProvider(p) {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(p));
    setProviderState(p);
  }

  function clearProvider() {
    localStorage.removeItem(STORAGE_KEY);
    setProviderState(null);
  }

  return (
    <ProviderContext.Provider value={{ provider, setProvider, clearProvider }}>
      {children}
    </ProviderContext.Provider>
  );
}

export function useProvider() {
  const ctx = useContext(ProviderContext);
  if (!ctx) throw new Error('useProvider must be used inside ProviderProvider');
  return ctx;
}
