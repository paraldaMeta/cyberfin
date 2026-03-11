import { createContext, useContext, useState, useEffect } from 'react';
import { LANGUAGES, getLanguage, setLanguage as saveLanguage, t as translate } from './translations';

const LanguageContext = createContext();

export const LanguageProvider = ({ children }) => {
  const [lang, setLangState] = useState(getLanguage());
  
  useEffect(() => {
    // Set document direction on mount
    const langConfig = LANGUAGES.find(l => l.code === lang);
    if (langConfig) {
      document.documentElement.dir = langConfig.dir;
    }
  }, [lang]);
  
  const setLang = (newLang) => {
    saveLanguage(newLang);
    setLangState(newLang);
    // Update document direction
    const langConfig = LANGUAGES.find(l => l.code === newLang);
    if (langConfig) {
      document.documentElement.dir = langConfig.dir;
    }
  };
  
  const t = (key) => translate(key, lang);
  
  return (
    <LanguageContext.Provider value={{ lang, setLang, t, languages: LANGUAGES }}>
      {children}
    </LanguageContext.Provider>
  );
};

export const useLanguage = () => {
  const context = useContext(LanguageContext);
  if (!context) {
    throw new Error('useLanguage must be used within LanguageProvider');
  }
  return context;
};
