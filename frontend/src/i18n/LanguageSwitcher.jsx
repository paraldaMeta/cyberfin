import { Globe } from 'lucide-react';
import { Button } from '../components/ui/button';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from '../components/ui/dropdown-menu';
import { useLanguage } from './LanguageContext';

export const LanguageSwitcher = () => {
  const { lang, setLang, languages } = useLanguage();
  
  const currentLang = languages.find(l => l.code === lang);
  
  return (
    <DropdownMenu>
      <DropdownMenuTrigger asChild>
        <Button variant="ghost" size="sm" className="h-8 gap-2 text-[#a1a1aa] hover:text-white hover:bg-[#1a1f2e]">
          <Globe className="w-4 h-4" />
          <span className="hidden sm:inline">{currentLang?.flag} {currentLang?.name}</span>
          <span className="sm:hidden">{currentLang?.flag}</span>
        </Button>
      </DropdownMenuTrigger>
      <DropdownMenuContent align="end" className="bg-[#141824] border-[#2a2f3e] min-w-[160px]">
        {languages.map((language) => (
          <DropdownMenuItem
            key={language.code}
            onClick={() => setLang(language.code)}
            className={`cursor-pointer hover:bg-[#1a1f2e] ${
              lang === language.code ? 'bg-[#1a1f2e] text-[#00f0ff]' : 'text-[#a1a1aa]'
            }`}
          >
            <span className="mr-2">{language.flag}</span>
            <span>{language.name}</span>
          </DropdownMenuItem>
        ))}
      </DropdownMenuContent>
    </DropdownMenu>
  );
};
