import { describe, it, expect } from 'vitest';
import { getHighlightTerms, highlightPageText } from '../../pages/PageView';

describe('getHighlightTerms', () => {
  it('returns meaningful words from a query', () => {
    const terms = getHighlightTerms('information retrieval systems');
    expect(terms).toContain('information');
    expect(terms).toContain('retrieval');
    expect(terms).toContain('systems');
  });

  it('filters out stopwords', () => {
    const terms = getHighlightTerms('what is the best way to search');
    expect(terms).not.toContain('what');
    expect(terms).not.toContain('the');
    expect(terms).not.toContain('is');
  });

  it('filters out words with 2 or fewer characters', () => {
    const terms = getHighlightTerms('go do it now');
    expect(terms).not.toContain('go');
    expect(terms).not.toContain('do');
    expect(terms).not.toContain('it');
  });

  it('returns empty array for empty query', () => {
    expect(getHighlightTerms('')).toEqual([]);
  });

  it('returns empty array for stopwords-only query', () => {
    const terms = getHighlightTerms('the a an is in of');
    expect(terms).toHaveLength(0);
  });

  it('is case-insensitive (lowercases terms)', () => {
    const terms = getHighlightTerms('Information Retrieval');
    expect(terms).toContain('information');
    expect(terms).toContain('retrieval');
  });

  it('handles single meaningful word', () => {
    const terms = getHighlightTerms('philosophy');
    expect(terms).toContain('philosophy');
  });

  it('handles multi-word query with mixed stopwords', () => {
    const terms = getHighlightTerms('the inverted index information retrieval');
    expect(terms).toContain('inverted');
    expect(terms).toContain('index');
    expect(terms).toContain('information');
    expect(terms).toContain('retrieval');
    expect(terms).not.toContain('the');
  });
});

describe('highlightPageText', () => {
  it('wraps matched terms with a mark tag', () => {
    const result = highlightPageText('information retrieval is important', ['information', 'retrieval']);
    expect(result).toContain('<mark');
    expect(result).toContain('information');
    expect(result).toContain('retrieval');
  });

  it('returns original text when terms array is empty', () => {
    const text = 'some page content here';
    expect(highlightPageText(text, [])).toBe(text);
  });

  it('is case-insensitive when highlighting', () => {
    const result = highlightPageText('Information Retrieval Systems', ['information']);
    expect(result).toContain('<mark');
    expect(result.toLowerCase()).toContain('information');
  });

  it('does not modify text when no terms match', () => {
    const text = 'completely unrelated content';
    const result = highlightPageText(text, ['xyz', 'abc']);
    expect(result).toBe(text);
  });

  it('highlights multiple terms independently', () => {
    const text = 'the inverted index is used in information retrieval';
    const result = highlightPageText(text, ['inverted', 'retrieval']);
    const markCount = (result.match(/<mark/g) || []).length;
    expect(markCount).toBe(2);
  });

  it('preserves non-matching text around highlights', () => {
    const text = 'hello world foo';
    const result = highlightPageText(text, ['world']);
    expect(result).toContain('hello');
    expect(result).toContain('foo');
    expect(result).toContain('<mark');
  });

  it('handles special regex characters in terms safely', () => {
    const text = 'c++ programming language';
    // Should not throw with special chars
    expect(() => highlightPageText(text, ['c++'])).not.toThrow();
  });

  it('applies orange background color in mark style', () => {
    const result = highlightPageText('index term here', ['index']);
    expect(result).toContain('#F89344');
  });
});
