"""
Text Preprocessing Module for NyayaShield
========================================

This module provides comprehensive text cleaning and normalization functions
for legal document processing and analysis.

"""

import re
import string
import unicodedata
from typing import List, Optional, Union
import nltk
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize, sent_tokenize
from nltk.stem import PorterStemmer, WordNetLemmatizer
from nltk.tag import pos_tag

# Download required NLTK data (run once)
try:
    nltk.data.find('tokenizers/punkt')
    nltk.data.find('corpora/stopwords')
    nltk.data.find('corpora/wordnet')
    nltk.data.find('taggers/averaged_perceptron_tagger')
except LookupError:
    nltk.download('punkt')
    nltk.download('stopwords')
    nltk.download('wordnet')
    nltk.download('averaged_perceptron_tagger')

# Initialize stemmer and lemmatizer
stemmer = PorterStemmer()
lemmatizer = WordNetLemmatizer()

# Legal-specific stopwords and terms
LEGAL_STOPWORDS = {
    'whereas', 'whereof', 'wherein', 'whereby', 'therefore', 'heretofore',
    'hereinafter', 'aforementioned', 'aforesaid', 'pursuant', 'thereof',
    'herein', 'hereunder', 'notwithstanding', 'provided', 'however'
}

# Common legal abbreviations and their expansions
LEGAL_ABBREVIATIONS = {
    'v.': 'versus',
    'vs.': 'versus',
    'etc.': 'et cetera',
    'i.e.': 'that is',
    'e.g.': 'for example',
    'cf.': 'compare',
    'ibid.': 'in the same place',
    'op. cit.': 'in the work cited',
    'supra': 'above',
    'infra': 'below',
    'ca.': 'circa',
    'c.': 'circa'
}


class TextPreprocessor:
    """
    A comprehensive text preprocessing class for legal documents.
    """
    
    def __init__(self, language='english'):
        """
        Initialize the preprocessor.
        
        Args:
            language (str): Language for stopwords (default: 'english')
        """
        self.language = language
        self.stop_words = set(stopwords.words(language))
        self.stop_words.update(LEGAL_STOPWORDS)
    
    def basic_clean(self, text: str) -> str:
        """
        Basic text cleaning: lowercase, remove extra whitespace.
        
        Args:
            text (str): Input text
            
        Returns:
            str: Cleaned text
        """
        if not isinstance(text, str):
            return ""
        
        # Convert to lowercase
        text = text.lower()
        
        # Remove extra whitespace
        text = re.sub(r'\s+', ' ', text)
        
        # Strip leading/trailing whitespace
        text = text.strip()
        
        return text
    
    def normalize_unicode(self, text: str) -> str:
        """
        Normalize Unicode characters to standard form.
        
        Args:
            text (str): Input text
            
        Returns:
            str: Unicode-normalized text
        """
        if not isinstance(text, str):
            return ""
        
        # Normalize to NFKD form and encode to ASCII
        text = unicodedata.normalize('NFKD', text)
        text = text.encode('ascii', 'ignore').decode('ascii')
        
        return text
    
    def expand_contractions(self, text: str) -> str:
        """
        Expand common English contractions.
        
        Args:
            text (str): Input text
            
        Returns:
            str: Text with expanded contractions
        """
        contractions = {
            "won't": "will not",
            "can't": "cannot",
            "n't": " not",
            "'re": " are",
            "'ve": " have",
            "'ll": " will",
            "'d": " would",
            "'m": " am"
        }
        
        for contraction, expansion in contractions.items():
            text = text.replace(contraction, expansion)
        
        return text
    
    def expand_legal_abbreviations(self, text: str) -> str:
        """
        Expand legal abbreviations to full forms.
        
        Args:
            text (str): Input text
            
        Returns:
            str: Text with expanded legal abbreviations
        """
        for abbrev, expansion in LEGAL_ABBREVIATIONS.items():
            text = re.sub(r'\b' + re.escape(abbrev) + r'\b', expansion, text, flags=re.IGNORECASE)
        
        return text
    
    def remove_punctuation(self, text: str, keep_periods: bool = False) -> str:
        """
        Remove punctuation from text.
        
        Args:
            text (str): Input text
            keep_periods (bool): Whether to keep periods for sentence structure
            
        Returns:
            str: Text without punctuation
        """
        if keep_periods:
            # Remove all punctuation except periods
            punctuation = string.punctuation.replace('.', '')
            text = text.translate(str.maketrans('', '', punctuation))
        else:
            # Remove all punctuation
            text = text.translate(str.maketrans('', '', string.punctuation))
        
        return text
    
    def remove_numbers(self, text: str, keep_years: bool = True) -> str:
        """
        Remove numbers from text with option to keep years.
        
        Args:
            text (str): Input text
            keep_years (bool): Whether to keep 4-digit years
            
        Returns:
            str: Text with numbers removed
        """
        if keep_years:
            # Keep 4-digit numbers (likely years) but remove others
            text = re.sub(r'\b(?<!\d)\d{1,3}(?!\d)\b', '', text)  # 1-3 digits
            text = re.sub(r'\b\d{5,}\b', '', text)  # 5+ digits
        else:
            # Remove all numbers
            text = re.sub(r'\d+', '', text)
        
        return text
    
    def remove_urls_emails(self, text: str) -> str:
        """
        Remove URLs and email addresses from text.
        
        Args:
            text (str): Input text
            
        Returns:
            str: Text without URLs and emails
        """
        # Remove URLs
        text = re.sub(r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+', '', text)
        
        # Remove email addresses
        text = re.sub(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', '', text)
        
        return text
    
    def remove_legal_citations(self, text: str) -> str:
        """
        Remove common legal citation patterns.
        
        Args:
            text (str): Input text
            
        Returns:
            str: Text without legal citations
        """
        # Remove patterns like "123 F.3d 456" or "456 U.S. 789"
        text = re.sub(r'\b\d+\s+[A-Z][a-z]*\.?\s*\d*d?\s+\d+\b', '', text)
        
        # Remove section references like "§ 123" or "Section 456"
        text = re.sub(r'§\s*\d+', '', text)
        text = re.sub(r'\bSection\s+\d+\b', '', text, flags=re.IGNORECASE)
        
        return text
    
    def tokenize_sentences(self, text: str) -> List[str]:
        """
        Split text into sentences.
        
        Args:
            text (str): Input text
            
        Returns:
            List[str]: List of sentences
        """
        return sent_tokenize(text)
    
    def tokenize_words(self, text: str) -> List[str]:
        """
        Split text into words/tokens.
        
        Args:
            text (str): Input text
            
        Returns:
            List[str]: List of tokens
        """
        return word_tokenize(text)
    
    def remove_stopwords(self, tokens: List[str], custom_stopwords: Optional[List[str]] = None) -> List[str]:
        """
        Remove stopwords from token list.
        
        Args:
            tokens (List[str]): List of tokens
            custom_stopwords (List[str], optional): Additional stopwords to remove
            
        Returns:
            List[str]: Filtered tokens
        """
        stop_words = self.stop_words.copy()
        if custom_stopwords:
            stop_words.update(custom_stopwords)
        
        return [token for token in tokens if token.lower() not in stop_words]
    
    def stem_tokens(self, tokens: List[str]) -> List[str]:
        """
        Apply stemming to tokens.
        
        Args:
            tokens (List[str]): List of tokens
            
        Returns:
            List[str]: Stemmed tokens
        """
        return [stemmer.stem(token) for token in tokens]
    
    def lemmatize_tokens(self, tokens: List[str]) -> List[str]:
        """
        Apply lemmatization to tokens with POS tagging.
        
        Args:
            tokens (List[str]): List of tokens
            
        Returns:
            List[str]: Lemmatized tokens
        """
        # Get POS tags
        pos_tags = pos_tag(tokens)
        
        lemmatized = []
        for token, pos in pos_tags:
            # Convert POS tag to WordNet format
            if pos.startswith('J'):
                pos_tag_wn = 'a'  # adjective
            elif pos.startswith('V'):
                pos_tag_wn = 'v'  # verb
            elif pos.startswith('N'):
                pos_tag_wn = 'n'  # noun
            elif pos.startswith('R'):
                pos_tag_wn = 'r'  # adverb
            else:
                pos_tag_wn = 'n'  # default to noun
            
            lemmatized.append(lemmatizer.lemmatize(token, pos_tag_wn))
        
        return lemmatized
    
    def filter_by_length(self, tokens: List[str], min_length: int = 2, max_length: int = 50) -> List[str]:
        """
        Filter tokens by length.
        
        Args:
            tokens (List[str]): List of tokens
            min_length (int): Minimum token length
            max_length (int): Maximum token length
            
        Returns:
            List[str]: Filtered tokens
        """
        return [token for token in tokens if min_length <= len(token) <= max_length]
    
    def preprocess_text(self, 
                       text: str,
                       normalize_unicode: bool = True,
                       expand_contractions: bool = True,
                       expand_abbreviations: bool = True,
                       remove_urls_emails: bool = True,
                       remove_citations: bool = True,
                       remove_punctuation: bool = True,
                       remove_numbers: bool = True,
                       keep_years: bool = True,
                       tokenize: bool = True,
                       remove_stopwords: bool = True,
                       lemmatize: bool = True,
                       stem: bool = False,
                       min_token_length: int = 2,
                       max_token_length: int = 50) -> Union[str, List[str]]:
        """
        Complete text preprocessing pipeline.
        
        Args:
            text (str): Input text
            normalize_unicode (bool): Normalize Unicode characters
            expand_contractions (bool): Expand contractions
            expand_abbreviations (bool): Expand legal abbreviations
            remove_urls_emails (bool): Remove URLs and emails
            remove_citations (bool): Remove legal citations
            remove_punctuation (bool): Remove punctuation
            remove_numbers (bool): Remove numbers
            keep_years (bool): Keep 4-digit years when removing numbers
            tokenize (bool): Return tokens instead of text
            remove_stopwords (bool): Remove stopwords
            lemmatize (bool): Apply lemmatization
            stem (bool): Apply stemming (ignored if lemmatize=True)
            min_token_length (int): Minimum token length
            max_token_length (int): Maximum token length
            
        Returns:
            Union[str, List[str]]: Processed text or tokens
        """
        if not isinstance(text, str):
            return "" if not tokenize else []
        
        # Basic cleaning
        processed_text = self.basic_clean(text)
        
        # Unicode normalization
        if normalize_unicode:
            processed_text = self.normalize_unicode(processed_text)
        
        # Expand contractions
        if expand_contractions:
            processed_text = self.expand_contractions(processed_text)
        
        # Expand legal abbreviations
        if expand_abbreviations:
            processed_text = self.expand_legal_abbreviations(processed_text)
        
        # Remove URLs and emails
        if remove_urls_emails:
            processed_text = self.remove_urls_emails(processed_text)
        
        # Remove legal citations
        if remove_citations:
            processed_text = self.remove_legal_citations(processed_text)
        
        # Remove punctuation
        if remove_punctuation:
            processed_text = self.remove_punctuation(processed_text)
        
        # Remove numbers
        if remove_numbers:
            processed_text = self.remove_numbers(processed_text, keep_years)
        
        # Clean up extra whitespace
        processed_text = re.sub(r'\s+', ' ', processed_text).strip()
        
        # Return text if tokenization not requested
        if not tokenize:
            return processed_text
        
        # Tokenization
        tokens = self.tokenize_words(processed_text)
        
        # Remove stopwords
        if remove_stopwords:
            tokens = self.remove_stopwords(tokens)
        
        # Lemmatization or stemming
        if lemmatize:
            tokens = self.lemmatize_tokens(tokens)
        elif stem:
            tokens = self.stem_tokens(tokens)
        
        # Filter by length
        tokens = self.filter_by_length(tokens, min_token_length, max_token_length)
        
        return tokens


# Convenience functions for backward compatibility and quick usage
def clean_text(text: str) -> str:
    """
    Basic text cleaning function (backward compatibility).
    
    Args:
        text (str): Input text
        
    Returns:
        str: Cleaned text
    """
    preprocessor = TextPreprocessor()
    return preprocessor.preprocess_text(
        text, 
        tokenize=False, 
        lemmatize=False, 
        remove_stopwords=False
    )


def preprocess_legal_text(text: str, return_tokens: bool = False) -> Union[str, List[str]]:
    """
    Preprocess legal text with optimal settings for legal documents.
    
    Args:
        text (str): Input legal text
        return_tokens (bool): Whether to return tokens or text
        
    Returns:
        Union[str, List[str]]: Processed text or tokens
    """
    preprocessor = TextPreprocessor()
    return preprocessor.preprocess_text(
        text,
        normalize_unicode=True,
        expand_contractions=True,
        expand_abbreviations=True,
        remove_urls_emails=True,
        remove_citations=False,  # Keep citations for legal context
        remove_punctuation=True,
        remove_numbers=True,
        keep_years=True,
        tokenize=return_tokens,
        remove_stopwords=True,
        lemmatize=True,
        min_token_length=2,
        max_token_length=50
    )


def extract_legal_entities(text: str) -> dict:
    """
    Extract legal entities and patterns from text.
    
    Args:
        text (str): Input text
        
    Returns:
        dict: Dictionary containing extracted entities
    """
    entities = {
        'case_citations': [],
        'statutes': [],
        'dates': [],
        'monetary_amounts': [],
        'court_names': []
    }
    
    # Extract case citations (simplified pattern)
    case_pattern = r'\b\d+\s+[A-Z][a-z]*\.?\s*\d*d?\s+\d+\b'
    entities['case_citations'] = re.findall(case_pattern, text)
    
    # Extract statute references
    statute_pattern = r'§\s*\d+(?:\.\d+)*|\bSection\s+\d+(?:\.\d+)*\b'
    entities['statutes'] = re.findall(statute_pattern, text, re.IGNORECASE)
    
    # Extract dates
    date_pattern = r'\b(?:\d{1,2}[/-]\d{1,2}[/-]\d{2,4}|\d{4}|\b(?:January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{1,2},?\s+\d{4})\b'
    entities['dates'] = re.findall(date_pattern, text, re.IGNORECASE)
    
    # Extract monetary amounts
    money_pattern = r'\$[\d,]+(?:\.\d{2})?'
    entities['monetary_amounts'] = re.findall(money_pattern, text)
    
    # Extract court names (simplified)
    court_pattern = r'\b(?:Supreme Court|Court of Appeals|District Court|Circuit Court|Superior Court|Municipal Court)\b'
    entities['court_names'] = re.findall(court_pattern, text, re.IGNORECASE)
    
    return entities


# Example usage and testing
if __name__ == "__main__":
    # Sample legal text for testing
    sample_text = """
    In the case of Smith v. Jones, 123 F.3d 456 (2020), the Supreme Court held that 
    the defendant's actions violated Section 42 of the Civil Rights Act. The plaintiff 
    was awarded $50,000 in damages. This decision was made on January 15, 2020.
    """
    
    print("Original text:")
    print(sample_text)
    print("\n" + "="*50 + "\n")
    
    # Initialize preprocessor
    preprocessor = TextPreprocessor()
    
    # Basic cleaning
    cleaned = preprocessor.basic_clean(sample_text)
    print("Basic cleaned:")
    print(cleaned)
    print("\n" + "-"*30 + "\n")
    
    # Full preprocessing (text)
    processed_text = preprocessor.preprocess_text(sample_text, tokenize=False)
    print("Fully processed text:")
    print(processed_text)
    print("\n" + "-"*30 + "\n")
    
    # Full preprocessing (tokens)
    processed_tokens = preprocessor.preprocess_text(sample_text, tokenize=True)
    print("Processed tokens:")
    print(processed_tokens)
    print("\n" + "-"*30 + "\n")
    
    # Extract legal entities
    entities = extract_legal_entities(sample_text)
    print("Extracted legal entities:")
    for entity_type, values in entities.items():
        if values:
            print(f"  {entity_type}: {values}")
    
    print("\n" + "="*50 + "\n")
    print("Preprocessing module loaded successfully!")
