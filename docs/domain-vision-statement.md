# Domain Vision Statement

The domain model will represent concept schemes to support search and retrieval of information resources relevant
to heliophysics researchers.
A concept scheme relates identified concepts by hierarchical and associative relationships using the SKOS standard.
Each concept has a preferred label and alternative labels in a scheme,
as well as more verbose text annotations either attached to its usage in the scheme or across all schemes.

These labels and annotations will support increasing both precision and recall
for search of an information-resource corpus by facilitating the tagging of corpus resources
with concepts from a concept scheme.
This support may involve computing and attaching labels and annotations of concepts associated with,
and in particular concepts hierarchically subsumed by,
those concepts in a scheme that are intentionally tagged to a corpus resource.

The lifecycle of a concept scheme will be represented to allow for 
persistent identification of all revisions of a scheme.
Revision tracking will support comparisons of scheme variants
for search performance against a common information-resource corpus
on the basis of computed performance metrics for precision, recall, etc.

The model will support applications that connect to an information-resource corpus
such as Astrophysics Data System (ADS) bibliographic records
in order to evaluate how a concept scheme may improve search performance
through tagging corpus resources with concept-scheme concepts,
re-indexing the corpus for search, and performing a suite of automated searches
against the search engine to collect known metrics.

## About

A <span class="term">Domain Vision Statement</span>[^1] is a short description (about one page)
of the <span class="term">core domain</span> and the value it will bring, the "value proposition."
Ignore those aspects that do not distinguish this domain model from others.
Show how the domain model serves and balances diverse interests.
Keep it narrow.
Write this statement early and revise it as you gain new insight.

It should be usable directly by the management and technical staff during all phases of development
to guide resource allocation, to guide modeling choices, and to educate team members.

## References

[^1]: [Domain Vision Statement](https://files.polyneme.xyz/domain-vision-statement-1696514386.pdf), pp415-6, in Evans, Eric. Domain-Driven Design: Tackling Complexity in the Heart of Software. Boston: Addison-Wesley, 2004.