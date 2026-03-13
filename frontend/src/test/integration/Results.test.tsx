import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { render, screen, waitFor, fireEvent } from '@testing-library/react';
import { MemoryRouter } from 'react-router';
import React from 'react';
import Results from '../../pages/Results';

// ── mocks ──────────────────────────────────────────────────────────────────

const mockNavigate = vi.fn();

vi.mock('react-router', async (importOriginal) => {
  const actual = await importOriginal<typeof import('react-router')>();
  return { ...actual, useNavigate: () => mockNavigate };
});

vi.mock('motion/react', () => ({
  motion: new Proxy({} as Record<string, unknown>, {
    get: (_target, tag: string) => {
      // eslint-disable-next-line @typescript-eslint/no-explicit-any
      return ({ children, initial: _i, animate: _a, transition: _t, ...rest }: any) =>
        React.createElement(tag, rest, children);
    },
  }),
}));

const MOCK_RESULTS = [
  {
    page_id: 'book_a_page_45',
    score: 92.34,
    book_title: 'Introduction to Information Retrieval',
    page_number: 45,
    display_page_number: '45',
    domain: 'Computer Science',
    preview: 'The inverted index is the most fundamental data structure in information retrieval.',
  },
  {
    page_id: 'book_b_page_112',
    score: 81.21,
    book_title: 'Modern Information Retrieval',
    page_number: 112,
    display_page_number: '112',
    domain: 'Computer Science',
    preview: 'TF-IDF weighting is a key concept in information retrieval systems.',
  },
];

const mockFetch = (results = MOCK_RESULTS, totalResults = MOCK_RESULTS.length, ok = true) => {
  vi.stubGlobal('fetch', vi.fn().mockResolvedValue({
    ok,
    json: () => Promise.resolve({ query: 'information retrieval', total_results: totalResults, results }),
    status: ok ? 200 : 500,
  }));
};

// Render with a search query in URL params
const renderResults = (search = '?q=information+retrieval&k=5') =>
  render(<MemoryRouter initialEntries={[`/results${search}`]}><Results /></MemoryRouter>);

// ── layout ──────────────────────────────────────────────────────────────────

describe('Results page — layout', () => {
  beforeEach(() => {
    mockNavigate.mockClear();
    mockFetch();
  });
  afterEach(() => vi.unstubAllGlobals());

  it('renders the page header with Search Results title', async () => {
    renderResults();
    await waitFor(() => expect(screen.getByText('Search Results')).toBeInTheDocument());
  });

  it('shows the query in the header', async () => {
    renderResults();
    await waitFor(() => expect(screen.getByText(/"information retrieval"/i)).toBeInTheDocument());
  });

  it('renders the Back to Search button', async () => {
    renderResults();
    await waitFor(() => expect(screen.getByRole('button', { name: /back to search/i })).toBeInTheDocument());
  });

  it('shows result count when results load', async () => {
    renderResults();
    await waitFor(() => expect(screen.getByText(/found/i)).toBeInTheDocument());
  });
});

// ── loading ──────────────────────────────────────────────────────────────────

describe('Results page — loading state', () => {
  afterEach(() => vi.unstubAllGlobals());

  it('shows loading indicator initially', () => {
    // Make fetch never resolve during this test
    vi.stubGlobal('fetch', vi.fn(() => new Promise(() => {})));
    renderResults();
    expect(screen.getByText(/searching/i)).toBeInTheDocument();
  });
});

// ── results ──────────────────────────────────────────────────────────────────

describe('Results page — search results', () => {
  beforeEach(() => {
    mockNavigate.mockClear();
    mockFetch();
  });
  afterEach(() => vi.unstubAllGlobals());

  it('renders both result cards after loading', async () => {
    renderResults();
    await waitFor(() => {
      expect(screen.getByText('Introduction to Information Retrieval')).toBeInTheDocument();
      expect(screen.getByText('Modern Information Retrieval')).toBeInTheDocument();
    });
  });

  it('shows rank badges 1 and 2', async () => {
    renderResults();
    await waitFor(() => {
      expect(screen.getByText('1')).toBeInTheDocument();
      expect(screen.getByText('2')).toBeInTheDocument();
    });
  });

  it('shows relevance score for top result as 100.0%', async () => {
    renderResults();
    await waitFor(() => expect(screen.getByText('100.0%')).toBeInTheDocument());
  });

  it('shows page numbers', async () => {
    renderResults();
    await waitFor(() => {
      expect(screen.getByText(/Page 45/i)).toBeInTheDocument();
      expect(screen.getByText(/Page 112/i)).toBeInTheDocument();
    });
  });

  it('shows domain badges', async () => {
    renderResults();
    await waitFor(() => {
      expect(screen.getAllByText('Computer Science').length).toBeGreaterThan(0);
    });
  });

  it('shows preview text', async () => {
    renderResults();
    await waitFor(() => {
      expect(screen.getByText(/most fundamental data structure/i)).toBeInTheDocument();
    });
  });

  it('shows matched terms section', async () => {
    renderResults();
    await waitFor(() => expect(screen.getAllByText(/matched terms/i).length).toBeGreaterThan(0));
  });

  it('shows View full page link', async () => {
    renderResults();
    await waitFor(() => {
      expect(screen.getAllByText(/view full page/i).length).toBeGreaterThan(0);
    });
  });

  it('respects topK — slices to requested number', async () => {
    mockFetch(MOCK_RESULTS, 2);
    renderResults('?q=retrieval&k=1');
    await waitFor(() => {
      // Only 1 result shown because k=1
      expect(screen.getByText('Introduction to Information Retrieval')).toBeInTheDocument();
      expect(screen.queryByText('Modern Information Retrieval')).not.toBeInTheDocument();
    });
  });
});

// ── empty ──────────────────────────────────────────────────────────────────

describe('Results page — empty results', () => {
  afterEach(() => vi.unstubAllGlobals());

  it('shows no results message when list is empty', async () => {
    mockFetch([], 0);
    renderResults('?q=xyzxyzxyz&k=5');
    await waitFor(() => expect(screen.getByText(/no results found/i)).toBeInTheDocument());
  });
});

// ── error ──────────────────────────────────────────────────────────────────

describe('Results page — error state', () => {
  afterEach(() => vi.unstubAllGlobals());

  it('shows backend unavailable message on fetch error', async () => {
    vi.stubGlobal('fetch', vi.fn().mockRejectedValue(new Error('Network Error')));
    renderResults();
    await waitFor(() => expect(screen.getByText(/backend unavailable/i)).toBeInTheDocument());
  });

  it('shows error message on non-ok response', async () => {
    mockFetch([], 0, false);
    renderResults();
    await waitFor(() => expect(screen.getByText(/backend unavailable/i)).toBeInTheDocument());
  });
});

// ── navigation ──────────────────────────────────────────────────────────────

describe('Results page — navigation', () => {
  beforeEach(() => {
    mockNavigate.mockClear();
    mockFetch();
  });
  afterEach(() => vi.unstubAllGlobals());

  it('Back to Search button navigates to /', async () => {
    renderResults();
    await waitFor(() => screen.getByRole('button', { name: /back to search/i }));
    fireEvent.click(screen.getByRole('button', { name: /back to search/i }));
    expect(mockNavigate).toHaveBeenCalledWith('/');
  });

  it('clicking a result card navigates to /page/:id with query param', async () => {
    renderResults();
    await waitFor(() => screen.getByText('Introduction to Information Retrieval'));
    fireEvent.click(screen.getByText('Introduction to Information Retrieval'));
    expect(mockNavigate).toHaveBeenCalledWith(
      expect.stringContaining('/page/book_a_page_45')
    );
  });
});
