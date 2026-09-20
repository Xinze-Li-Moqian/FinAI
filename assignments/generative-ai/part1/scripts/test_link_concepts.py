"""Focused regression checks for transcript linking; no network or corpus writes."""
import unittest
from link_concepts import Linker, display_text, protected_spans

class LinkingTests(unittest.TestCase):
    def test_boundaries_case_possessive_and_hyphen(self):
        linker=Linker({'Finance/Interest':['interest rate'],'Finance/Banks':['central bank']})
        source="INTEREST RATES and interest‑rate; disinterest rates; central bank's reserves and central banks’ reserves."
        result,hits,_,_=linker.transform(source)
        self.assertEqual(sum(hits.values()),4)
        self.assertIn('|INTEREST RATES]]',result)
        self.assertIn('|interest‑rate]]',result)
        self.assertIn('disinterest rates',result)
        self.assertIn("|central bank's]]",result)
        self.assertEqual(display_text(result),source)
    def test_longest_overlap(self):
        linker=Linker({'Finance/Interest':['interest rate'],'Finance/Real':['real interest rate'],'Finance/Mortgage':['mortgage interest rate']})
        result,hits,_,_=linker.transform('real interest rates; mortgage-interest-rate; interest rate')
        self.assertEqual(hits,{'Finance/Real':1,'Finance/Mortgage':1,'Finance/Interest':1})
    def test_conflict_is_skipped_without_shorter_fallback(self):
        linker=Linker({'Finance/A':['policy rate'],'Finance/B':['policy-rate'],'Finance/C':['rate']})
        result,hits,skips,_=linker.transform('policy rates; rate')
        self.assertEqual(result,'policy rates; [[Finance/C|rate]]')
        self.assertEqual(skips,{'conflict: policy rates':1})
        self.assertTrue(linker.conflicts)
    def test_metadata_links_code_urls_and_headings_are_protected(self):
        linker=Linker({'Finance/Bitcoin':['Bitcoin']})
        prefix='---\ntitle: Bitcoin\n---\n# Bitcoin\n\n'
        source=prefix+'Bitcoin [Bitcoin](https://host/a(b(c))) [[Other|Bitcoin]] [Bitcoin][ref] `Bitcoin`\n```python\nBitcoin\n```\n    Bitcoin\nhttps://site/Bitcoin\n<https://site/Bitcoin>\n## Bitcoin\n[ref]: https://site/Bitcoin\n'
        result,hits,_,_=linker.transform(source)
        self.assertEqual(sum(hits.values()),1)
        self.assertTrue(result.startswith(prefix))
        self.assertEqual(display_text(result),display_text(source))
        self.assertEqual(linker.transform(result)[0],result)
    def test_unclosed_fence_and_multi_backtick(self):
        linker=Linker({'Finance/Bitcoin':['Bitcoin']})
        source='``Bitcoin ` sample``\n~~~\nBitcoin'
        self.assertEqual(linker.transform(source)[0],source)
    def test_ambiguous_contexts(self):
        linker=Linker({'Finance/Bond':['bond'],'Finance/Silver':['silver'],'Finance/Mortgage':['mortgage']})
        source='chemical bond and silver lining and mortgage-backed securities; bonds and silver bullion and mortgage loans'
        result,hits,skips,_=linker.transform(source)
        self.assertEqual(sum(hits.values()),3)
        self.assertEqual(sum(skips.values()),3)
        self.assertEqual(display_text(result),source)
    def test_punctuation_acronyms_and_existing_manual_links(self):
        linker=Linker({'Finance/QE':['QE'],'Finance/Retirement':['401(k)'],'Finance/Law':["Gresham's law"]})
        source='qe, 401(k), Gresham’s law; [[Manual|QE]]; equity.\n'
        result,hits,_,_=linker.transform(source)
        self.assertEqual(sum(hits.values()),3)
        self.assertIn('[[Manual|QE]]',result)
        self.assertEqual(display_text(result),display_text(source))
        self.assertEqual(linker.transform(result)[0],result)

class GraphRegressionTests(unittest.TestCase):
    def test_financial_options_context_only(self):
        linker=Linker({'Finance/Options':['options']})
        source='trading options and spx options and options trading; some better options and two options'
        result,hits,skips,_=linker.transform(source)
        self.assertEqual(sum(hits.values()),3)
        self.assertEqual(sum(skips.values()),2)
        self.assertEqual(display_text(result),source)
    def test_automation_requires_employment_context(self):
        linker=Linker({'Finance/Automation':['automation']})
        source='Automation will take your job.\n\nI configured automation in my home.'
        result,hits,skips,_=linker.transform(source)
        self.assertEqual(sum(hits.values()),1)
        self.assertEqual(sum(skips.values()),1)
        self.assertEqual(linker.transform(result)[0],result)
    def test_currency_escaping_preserves_display(self):
        self.assertEqual(display_text(r'Cost $20 and \$30 [[Finance/X|inflation]].'), 'Cost $20 and $30 inflation.')

class FullReadingRegressionTests(unittest.TestCase):
    def test_subjective_value_plural(self):
        linker=Linker({'Finance/Value':['subjective value']})
        source='Our subjective values differ.'
        result,hits,_,_=linker.transform(source)
        self.assertEqual(sum(hits.values()),1)
        self.assertEqual(display_text(result),source)
    def test_profitable_requires_financial_context(self):
        linker=Linker({'Finance/Profit':['profitable']})
        source='Our business is profitable after costs.\n\nThis was a profitable conversation about art.'
        result,hits,skips,_=linker.transform(source)
        self.assertEqual(sum(hits.values()),1)
        self.assertEqual(sum(skips.values()),1)
    def test_budgeting_requires_household_context(self):
        linker=Linker({'Finance/Budget':['budgeting']})
        source='My wife is good at budgeting and cutting expenses.\n\nThe government is budgeting for next year.'
        result,hits,skips,_=linker.transform(source)
        self.assertEqual(sum(hits.values()),1)
        self.assertEqual(sum(skips.values()),1)

if __name__=='__main__':unittest.main()
