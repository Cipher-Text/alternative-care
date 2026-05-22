/**
 * Medicine Autocomplete Component
 * Smart search with type-ahead for selecting medicines
 */

'use client';

import { useState, useEffect, useRef } from 'react';
import { useSearchMedicines } from '@/lib/hooks/useMedicines';
import { Input } from '@/components/ui/input';
import { Badge } from '@/components/ui/badge';
import { Card } from '@/components/ui/card';
import { Search, Loader2 } from 'lucide-react';
import type { MedicalSystem, MedicineSearchResult } from '@/types/medicine';

interface MedicineAutocompleteProps {
  onSelect: (medicine: MedicineSearchResult) => void;
  placeholder?: string;
  defaultValue?: string;
  disabled?: boolean;
}

export function MedicineAutocomplete({
  onSelect,
  placeholder = 'Search medicines...',
  defaultValue = '',
  disabled = false,
}: MedicineAutocompleteProps) {
  const [searchTerm, setSearchTerm] = useState(defaultValue);
  const [debouncedTerm, setDebouncedTerm] = useState(defaultValue);
  const [showResults, setShowResults] = useState(false);
  const [selectedIndex, setSelectedIndex] = useState(-1);

  const wrapperRef = useRef<HTMLDivElement>(null);

  const { data: results = [], isLoading } = useSearchMedicines({
    q: debouncedTerm,
    limit: 10,
  });

  // Debounce search term
  useEffect(() => {
    const timer = setTimeout(() => {
      setDebouncedTerm(searchTerm);
    }, 300);

    return () => clearTimeout(timer);
  }, [searchTerm]);

  // Show results when search returns data
  useEffect(() => {
    if (debouncedTerm && results.length > 0) {
      setShowResults(true);
    }
  }, [debouncedTerm, results]);

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
    setSearchTerm(medicine.name_en);
    setShowResults(false);
    setSelectedIndex(-1);
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
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
            setShowResults(true);
            setSelectedIndex(-1);
          }}
          onKeyDown={handleKeyDown}
          onFocus={() => {
            if (debouncedTerm && results.length > 0) {
              setShowResults(true);
            }
          }}
          placeholder={placeholder}
          className="pl-10 pr-10"
          disabled={disabled}
        />
        {isLoading && (
          <Loader2 className="absolute right-3 top-1/2 transform -translate-y-1/2 w-4 h-4 animate-spin text-gray-400" />
        )}
      </div>

      {/* Results Dropdown */}
      {showResults && results.length > 0 && (
        <Card className="absolute z-50 w-full mt-2 max-h-96 overflow-y-auto shadow-lg">
          {results.map((medicine, index) => (
            <div
              key={medicine.id}
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
                        Global
                      </Badge>
                    )}
                  </div>

                  {medicine.name_bn && (
                    <p className="text-xs text-gray-600 truncate mb-2">{medicine.name_bn}</p>
                  )}

                  <div className="flex items-center gap-2 flex-wrap">
                    <Badge className={`text-xs ${getSystemColor(medicine.system)}`}>
                      {medicine.system.charAt(0).toUpperCase() + medicine.system.slice(1)}
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
                      <span className="text-gray-500">Also known as: </span>
                      <span className="font-medium text-blue-600">{medicine.matched_alias}</span>
                    </div>
                  )}

                  {/* Show dosage guidance preview if available */}
                  {medicine.dosage_guidance_en && (
                    <p className="text-xs text-gray-500 mt-2 truncate">
                      <span className="font-medium">Dosage: </span>
                      {medicine.dosage_guidance_en}
                    </p>
                  )}
                </div>

                {/* Match rank indicator */}
                {medicine.rank !== undefined && (
                  <div className="text-xs text-gray-400 shrink-0">
                    {Math.round(medicine.rank * 100)}%
                  </div>
                )}
              </div>
            </div>
          ))}
        </Card>
      )}

      {/* No results message */}
      {showResults && debouncedTerm && !isLoading && results.length === 0 && (
        <Card className="absolute z-50 w-full mt-2 p-4 shadow-lg">
          <p className="text-sm text-gray-500 text-center">No medicines found</p>
        </Card>
      )}
    </div>
  );
}
