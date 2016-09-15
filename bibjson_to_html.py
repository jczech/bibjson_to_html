#!/usr/bin/env python3

import json
import re
import argparse


# Convert a BibJSON file to HTML. It was originally intended to be general, but
# is becoming increasingly tailored to one specific purpose
# (http://mmbios.org/publications). Also, it now requires the use of the
# original BibTeX file. :(

link_dict = {
    "DBP1": "research/driving-biomedical-projects/glutamate-transport",
    "DBP2": "research/driving-biomedical-projects/synaptic-signaling",
    "DBP3": "research/driving-biomedical-projects/dat-function",
    "DBP4": "research/driving-biomedical-projects/t-cell-signaling",
    "DBP5": "research/driving-biomedical-projects/neural-circuits",
    "TRD1": "research/technology-research-and-development/molecular-modeling",
    "TRD2": "research/technology-research-and-development/cell-modeling",
    "TRD3": "research/technology-research-and-development/image-processing",
    "CSP":  "research/collaboration-service",
}


def get_year(item):
    return int(item['issued']['date-parts'][0][0])


def bibjson_to_html(bibjson_filename, bibtex_filename):
    # The bibjson file doesn't contain the mendeley tags, so we have to parse
    # them from the bibtex file. Maybe we should just get everything from the
    # bibtex file using pyparsing or something like that.
    with open(bibtex_filename) as bibtex_file:
        try:
            lines = bibtex_file.readlines()
            tag = ""
            tag_dict = {}
            for l in lines:
                if ("mendeley-tags" in l):
                    tag = l.split(" ")[2]
                    tag = tag[1:-3]
                    tag_list = tag.split(",")
                    tag_list = [t.split("-")[1] for t in tag_list]
                elif ("pmid" in l):
                    pmid = l.split(" ")[2]
                    pmid = "".join(i for i in pmid if i.isdigit())
                    if tag:
                        tag_dict[pmid] = tag_list
                    tag = ""
        except ValueError as e:
            print("Cannot load BibTeX file: %s" % e)
            return

    with open(bibjson_filename) as json_file:
        try:
            bib_data = json.load(json_file)
        except ValueError as e:
            print("Cannot load JSON file: %s" % e)
            return

    caps = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'
    prev_year_int = 0
    html_str = "<meta charset=\"UTF-8\">\n"
    # Bibliography in reverse chronological order (newest first)
    bib_data = sorted(bib_data, key=get_year, reverse=True)

    for bib_entry in bib_data:
        year_int = int(bib_entry['issued']['date-parts'][0][0])
        if (year_int != prev_year_int):
            if (prev_year_int != 0):
                html_str += "\t</ul>\n</div>\n"
            html_str += "<h1 id=\"%d\"><span style=\"color: #993300;\">%d\
                         </span>\n</h1>\n" % (year_int, year_int)
            html_str += "<div class=\"biblio\">\n\t<ul>\n"
        year = "<span class=\"pubdate\">(%d)</span>" % year_int
        authors = ""
        # Convert authors name to "Surname First-Middle initials"
        # (e.g. "Czech JA")
        for idx, author in enumerate(bib_entry['author']):
            if (idx > 5):
                authors += "et al  "
                break
            try:
                surname = author['family']
                initials = "".join([l for l in author['given'] if l in caps])
                authors += "<span class=\"author\">%s %s</span>, " % (
                    surname, initials)
            # There's an entry but no surname, so it's prolly an institution
            except KeyError:
                authors += "<span class=\"author\">%s</span>, " % (
                    author['literal'])
        authors = authors[:-2]
        journal = bib_entry['container-title']
        journal = "<span class=\"journal\">%s</span>" % journal
        url = bib_entry['URL'].split(" ")[0]
        title = bib_entry['title']
        # XXX: regex is unsafe against malicious code. unlikely issue here.
        title = re.sub('<[^<]+?>', '', title)
        if title.endswith("."):
            title = title[:-1]
        title = (
            "<span class=\"title\" style=\"color: #2ebbbd;\">"
            "<a href = \"%s\">%s</a></span>" % (url, title))
        vol = bib_entry['volume']
        try:
            issue = bib_entry['issue']
            vol_issue = "<span class=\"volume\">%s(%s):</span>" % (vol, issue)

        except KeyError:
            vol_issue = "<span class=\"volume\">%s:</span>" % (vol)
        pages = bib_entry['page']
        pages = "<span class=\"mpgn\">%s</span>" % pages
        pmid = bib_entry['PMID']
        tags = ""
        if pmid in tag_dict:
            for tag in tag_dict[pmid]:
                if tag.startswith("TRD"):
                    tag_type = "trd_pub"
                    url = link_dict[tag]
                elif tag.startswith("DBP"):
                    tag_type = "dbp_pub"
                    url = link_dict[tag]
                elif tag.startswith("CSP"):
                    tag_type = "csp_pub"
                    url = "research/collaboration-service"
                url = "http://mmbios.org/%s" % url
                tags += (
                    "<a href=\"%s\" class=%s>%s</a> " % (url, tag_type, tag))
        pmid = "<span class=\"pmid\">PMID:%s</span>" % pmid
        doi = bib_entry['DOI']
        entry = "<p>%s. %s %s. <i>%s</i>. %s%s. doi: %s. %s %s" % (
            authors, year, title, journal, vol_issue, pages, doi, pmid, tags)
        html_str += "\t\t<li>\n"
        html_str += "\t\t\t%s\n" % entry
        html_str += "\t\t\t</p>\n"
        html_str += "\t\t</li>\n"
        prev_year_int = year_int
    html_str += "\t</ul>\n</div>\n"

    with open("output.html", 'w') as out:
        out.write(html_str)


def setup_argparser():
    parser = argparse.ArgumentParser(
        description="Convert BibJSON to marked up HTML:")
    parser.add_argument("bibjson", help="BibJSON file to be converted")
    parser.add_argument("bibtex", help="BibTeX file to be converted")
    return parser.parse_args()


def main():
    args = setup_argparser()
    bibjson_to_html(args.bibjson, args.bibtex)


if __name__ == "__main__":
    main()