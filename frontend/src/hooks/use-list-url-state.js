import { getRouteApi } from "@tanstack/react-router";
import { useCallback, useEffect, useState } from "react";

import { useDebouncedValue } from "@/hooks/use-debounced-value";
import { cleanListSearch } from "@/lib/list-search";

export function useListUrlState(routePath) {
  const routeApi = getRouteApi(routePath);
  const searchParams = routeApi.useSearch();
  const navigate = routeApi.useNavigate();

  const updateSearch = useCallback(
    (updates, { resetPage = false } = {}) => {
      navigate({
        search: (prev) =>
          cleanListSearch({
            ...prev,
            ...updates,
            ...(resetPage ? { page: 1 } : {}),
          }),
      });
    },
    [navigate],
  );

  const setPage = useCallback(
    (page) => {
      updateSearch({ page: page <= 1 ? undefined : page });
    },
    [updateSearch],
  );

  return {
    searchParams,
    page: searchParams.page ?? 1,
    updateSearch,
    setPage,
  };
}

export function useDebouncedListSearch(routePath, key = "search", delay = 300) {
  const { searchParams, updateSearch } = useListUrlState(routePath);
  const urlValue = searchParams[key] ?? "";
  const [inputValue, setInputValue] = useState(urlValue);
  const debouncedValue = useDebouncedValue(inputValue, delay);

  useEffect(() => {
    setInputValue(urlValue);
  }, [urlValue]);

  useEffect(() => {
    if (debouncedValue === urlValue) return;
    updateSearch({ [key]: debouncedValue || undefined }, { resetPage: true });
  }, [debouncedValue, key, updateSearch, urlValue]);

  return { inputValue, setInputValue, debouncedValue };
}
