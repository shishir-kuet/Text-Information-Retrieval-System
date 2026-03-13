import { describe, it, expect } from 'vitest';
import { getMatchedTerms, highlightText, normalizeScore } from '../../pages/Results';

describe('getMatchedTerms', () => {
  it('returns meaningful words from a query', () => {
    const terms = getMatchedTerms('information retrieval systems');
    expect(terms).toContain('information');
    expect(terms).toContain('retrieval');
    expect(terms).toContain('systems');
  });

  it('filters out stopwords', () => {
    const terms = getMatchedTerms('what is the best way to search');
    expect(terms).not.toContain('what');
    expect(terms).not.toContain('the');
    expect(terms).not.toContain('is');
  });

  it('filters out words shorter than 3 characters', () => {
    const terms = getMatchedTerms('AI in NLP');
    // 'in' is a stopword and also <= 2 chars; 'AI' and 'NLP' are 2/3 chars
    expect(terms).not.toContain('in');
  });

  it('returns empty array for empty query', () => {
    expect(getMatchedTerms('')).toEqual([]);
  });

  it('is case-insensitive (returns lowercase terms)', () => {
    const terms = getMatchedTerms('Information Retrieval');
    expect(terms).toContain('information');
    expect(terms).toContain('retrieval');
  });
});

describe('highlightText', () => {
  it('wraps matched terms with a mark tag', () => {
    const result = highlightText('information retrieval is great', ['information', 'retrieval']);
    expect(result).toContain('<mark');
    expect(result).toContain('information');
    expect(result).toContain('retrieval');
  });

  it('returns original text when terms array is empty', () => {
    const text = 'hello world';
    expect(highlightText(text, [])).toBe(text);
  });

  it('is case-insensitive when highlighting', () => {
    const result = highlightText('Information Retrieval', ['information']);
    expect(result).toContain('<mark');
  });

  it('does not alter text content outside matched terms', () => {
    const result = highlightText('hello world test', ['world']);
    expect(result).toContain('hello');
    expect(result).toContain('test');
  });
});

describe('normalizeScore', () => {
  it('returns 100 for the top score', () => {
    expect(normalizeScore(50, 50)).toBe(100);
  });

  it('returns proportional percentage', () => {
    expect(normalizeScore(25, 50)).toBe(50);
  });

  it('returns 0 when maxScore is 0', () => {
    expect(normalizeScore(0, 0)).toBe(0);
  });

  it('caps at 100 even if score exceeds maxScore', () => {
    expect(normalizeScore(200, 100)).toBe(100);
  });
});
