/**
 * Medicine Autocomplete Component
 * Smart search with type-ahead for selecting medicines
 */

'use client';

import { useState, useEffect, useRef } from 'react';
import { useTranslations } from 'next-intl';
import { useQuery } from 'react-query';
import { medicinesApi } from '@/lib/api/medicines';
import { useSearchMedicines } from '@/lib/hooks/useMedicines';
import { Input } from '@/components/ui/input';
import { Badge } from '@/components/ui/badge';
import { Card } from '@/components/ui/card';
import { ChevronDown, Search, Loader2 } from 'lucide-react';
import type { MedicalSystem, MedicineListItem, MedicineSearchResult } from '@/types/medicine';

const BROWSE_LIMIT = 50;

/** A plain list row, shown in the shape of a search result */
const asResult = (m: MedicineListItem): MedicineSearchResult => ({
  id: m.id,
  name_en: m.name_en,
  name_bn: m.name_bn,
  system: m.system,
  potency: m.potency,
  category: m.category,
  matched_alias: null,
  rank: 0,
  is_global: m.is_global,
});

interface MedicineAutocompleteProps {
  onSelect: (medicine: MedicineSearchResult) => void;
  placeholder?: string;
  defaultValue?: string;
  disabled?: boolean;
  /** Called on every keystroke, so a name that is not in the database can still be typed (free text) */
  onTextChange?: (text: string) => void;
  /** What the box shows after a pick (default: the English name); a prescription row shows name and potency */
  formatSelected?: (medicine: MedicineSearchResult) => string;
  autoFocus?: boolean;
  invalid?: boolean;
}

export function MedicineAutocomplete({
  onSelect,
  placeholder: placeholderProp,
  defaultValue = '',
  disabled = false,
  onTextChange,
  formatSelected,
  autoFocus = false,
  invalid = false,
}: MedicineAutocompleteProps) {
  const t = useTranslations('medicineAutocompleteUi');
  const placeholder = placeholderProp ?? t('defaultPlaceholder');
  const [searchTerm, setSearchTerm] = useState(defaultValue);
  const [debouncedTerm, setDebouncedTerm] = useState(defaultValue);
  const [showResults, setShowResults] = useState(false);
  const [selectedIndex, setSelectedIndex] = useState(-1);

  const wrapperRef = useRef<HTMLDivElement>(null);

  // Nothing typed: the box is a plain dropdown of the medicine list (A to Z). Typing searches by name or alias.
  const browsing = debouncedTerm.trim() === '';
  const { data: found = [], isLoading: searching } = useSearchMedicines({
    q: debouncedTerm,
    limit: 10,
  });
  const { data: browseList = [], isLoading: loadingList } = useQuery(
    ['medicines', 'browse', BROWSE_LIMIT],
    () => medicinesApi.list({ limit: BROWSE_LIMIT }),
    { enabled: showResults && browsing, staleTime: 60000 }
  );
  const results = browsing ? browseList.map(asResult) : found;
  const isLoading = browsing ? loadingList && showResults : searching;

  // Debounce search term
  useEffect(() => {
    const timer = setTimeout(() => {
      setDebouncedTerm(searchTerm);
    }, 300);

    return () => clearTimeout(timer);
  }, [searchTerm]);

  // Close dropdown when clicking outside
  useEffect(() => {
    function handleClickOutside(event: MouseEvent) {
      if (wrapperRef.current && !wrapperRef.current.contains(event.target as Node)) {
        setShowResults(false);
      }
    }

    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  const handleSelect = (medicine: MedicineSearchResult) => {
    onSelect(medicine);
    setSearchTerm(formatSelected ? formatSelected(medicine) : medicine.name_en);
    setShowResults(false);
    setSelectedIndex(-1);
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'ArrowDown' && !showResults) {
      e.preventDefault();
      setShowResults(true);
      return;
    }
    if (!showResults || results.length === 0) return;

    switch (e.key) {
      case 'ArrowDown':
        e.preventDefault();
        setSelectedIndex((prev) => (prev < results.length - 1 ? prev + 1 : prev));
        break;
      case 'ArrowUp':
        e.preventDefault();
        setSelectedIndex((prev) => (prev > 0 ? prev - 1 : -1));
        break;
      case 'Enter':
        e.preventDefault();
        if (selectedIndex >= 0 && results[selectedIndex]) {
          handleSelect(results[selectedIndex]);
        }
        break;
      case 'Escape':
        setShowResults(false);
        setSelectedIndex(-1);
        break;
    }
  };

  const getSystemColor = (system: MedicalSystem) => {
    switch (system) {
      case 'homeopathy':
        return 'bg-blue-100 text-blue-800';
      case 'ayurveda':
        return 'bg-green-100 text-green-800';
      case 'unani':
        return 'bg-purple-100 text-purple-800';
      case 'herbal':
        return 'bg-orange-100 text-orange-800';
      default:
        return 'bg-gray-100 text-gray-800';
    }
  };

  return (
    <div ref={wrapperRef} className="relative w-full">
      <div className="relative">
        <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-gray-400" />
        <Input
          value={searchTerm}
          onChange={(e) => {
            setSearchTerm(e.target.value);
            onTextChange?.(e.target.value);
            setShowResults(true);
            setSelectedIndex(-1);
          }}
          onKeyDown={handleKeyDown}
          onFocus={() => setShowResults(true)}
          onClick={() => setShowResults(true)}
          placeholder={placeholder}
          className="pl-10 pr-10"
          disabled={disabled}
          autoFocus={autoFocus}
          aria-invalid={invalid || undefined}
          role="combobox"
          aria-label={placeholder ? placeholder.replace(/\.{3}$/, '') : 'Search medicines'}
          aria-autocomplete="list"
          aria-expanded={showResults && results.length > 0}
          aria-controls="medicine-results"
          aria-activedescendant={selectedIndex >= 0 ? `medicine-option-${selectedIndex}` : undefined}
        />
        {isLoading ? (
          <Loader2 className="absolute right-3 top-1/2 transform -translate-y-1/2 w-4 h-4 animate-spin text-gray-400" />
        ) : (
          <button
            type="button"
            tabIndex={-1}
            disabled={disabled}
            aria-label={t('toggleAria')}
            onClick={() => setShowResults((open) => !open)}
            className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-400"
          >
            <ChevronDown className="w-4 h-4" />
          </button>
        )}
      </div>

      {/* Results Dropdown */}
      {showResults && results.length > 0 && (
        <Card id="medicine-results" role="listbox" className="absolute z-50 w-full mt-2 max-h-96 overflow-y-auto shadow-lg">
          {browsing && <p className="border-b px-4 py-2 text-xs text-gray-500">{t('browseHint', { count: BROWSE_LIMIT })}</p>}
          {results.map((medicine, index) => (
            <div
              key={medicine.id}
              id={`medicine-option-${index}`}
              role="option"
              aria-selected={index === selectedIndex}
              className={`p-4 cursor-pointer border-b last:border-b-0 transition-colors ${
                index === selectedIndex ? 'bg-blue-50' : 'hover:bg-gray-50'
              }`}
              onClick={() => handleSelect(medicine)}
              onMouseEnter={() => setSelectedIndex(index)}
            >
              <div className="flex items-start justify-between gap-3">
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2 mb-1">
                    <h4 className="font-semibold text-sm truncate">{medicine.name_en}</h4>
                    {medicine.is_global && (
                      <Badge variant="outline" className="text-xs shrink-0">
                        {t('global')}
                      </Badge>
                    )}
                  </div>

                  {medicine.name_bn && (
                    <p className="text-xs text-gray-600 truncate mb-2">{medicine.name_bn}</p>
                  )}

                  <div className="flex items-center gap-2 flex-wrap">
                    <Badge className={`text-xs ${getSystemColor(medicine.system)}`}>
                      {t.has(`system.${medicine.system}`)
                        ? t(`system.${medicine.system}`)
                        : medicine.system.charAt(0).toUpperCase() + medicine.system.slice(1)}
                    </Badge>

                    {medicine.potency && (
                      <Badge variant="outline" className="text-xs">
                        {medicine.potency}
                      </Badge>
                    )}

                    {medicine.category && (
                      <span className="text-xs text-gray-500">{medicine.category}</span>
                    )}
                  </div>

                  {/* Show matched alias if search matched an alias */}
                  {medicine.matched_alias && (
                    <div className="mt-2 text-xs">
                      <span className="text-gray-500">{t('alsoKnownAs')}</span>
                      <span className="font-medium text-blue-600">{medicine.matched_alias}</span>
                    </div>
                  )}

                  {/* Show dosage guidance preview if available */}
                  {medicine.dosage_guidance_en && (
                    <p className="text-xs text-gray-500 mt-2 truncate">
                      <span className="font-medium">{t('dosage')}</span>
                      {medicine.dosage_guidance_en}
                    </p>
                  )}
                </div>

              </div>
            </div>
          ))}
        </Card>
      )}

      {/* No results message */}
      {showResults && !browsing && !isLoading && results.length === 0 && (
        <Card className="absolute z-50 w-full mt-2 p-4 shadow-lg">
          <p className="text-sm text-gray-500 text-center">{t('noResults')}</p>
        </Card>
      )}
    </div>
  );
}
