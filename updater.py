# Generates a LaTeX resume from a template file and data fetched from GitHub and LinkedIn APIs
# The generated resume is saved to a file named resume.tex

import requests
import os
import json
from dotenv import load_dotenv
from models.linkedin import LinkedinProfile
from models.github import GithubResponse
import calendar

load_dotenv()

GITHUB_API_URL = "https://api.github.com/graphql"
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")

LINKEDIN_API_URL = "https://li-data-scraper.p.rapidapi.com/get-profile-data-by-url"
LINKEDIN_API_KEY = os.getenv("LINKEDIN_API_KEY")
LINKEDIN_PROFILE_URL = os.getenv("LINKEDIN_PROFILE_URL")

TEMPLATE_FILE = "misc/template.tex"
OUTPUT_FILE = "resume.tex"
GITHUB_DATA_FILE = "github_data.json"
LINKEDIN_DATA_FILE = "linkedin_data.json"
local = os.getenv("LOCAL")

def fetch_github_data(query: str) -> GithubResponse:
    if local and os.path.exists(GITHUB_DATA_FILE):
        with open(GITHUB_DATA_FILE, "r") as file:
            data = json.load(file)
    else:
        headers = {
            "Authorization": f"Bearer {GITHUB_TOKEN}",
            "Content-Type": "application/json"
        }
        response = requests.post(GITHUB_API_URL, json={"query": query}, headers=headers)
        if response.status_code == 200:
            data = response.json()["data"]
            with open(GITHUB_DATA_FILE, "w") as file:
                json.dump(data, file)
        else:
            raise Exception(f"Github query failed: {response.status_code}: {response.text}")
    return GithubResponse.parse_obj(data)

def fetch_linkedin_data() -> LinkedinProfile:
    if local and os.path.exists(LINKEDIN_DATA_FILE):
        with open(LINKEDIN_DATA_FILE, "r") as file:
            data = json.load(file)
    else:
        headers = {
            "x-rapidapi-key": LINKEDIN_API_KEY,
            "x-rapidapi-host": "li-data-scraper.p.rapidapi.com",
        }
        params = {"url": LINKEDIN_PROFILE_URL}
        response = requests.get(LINKEDIN_API_URL, headers=headers, params=params)
        if response.status_code == 200:
            data = response.json()
            with open(LINKEDIN_DATA_FILE, "w") as file:
                json.dump(data, file)
        else:
            raise Exception(f"LinkedIn fetch failed: {response.status_code}: {response.text}")
    return LinkedinProfile.parse_obj(data)

def update_latex_template(data: GithubResponse, linkedin_data: LinkedinProfile) -> None:
    try:
        with open(TEMPLATE_FILE, "r") as template_file:
            template_content = template_file.read()

        
        repositories = data.viewer.repositories
        repo_entries = "".join([
            f"\\item \\textbf{{\\href{{{repo.url}}}{{{repo.name}}}}}\n"
            f"\n{next((proj.description for proj in linkedin_data.projects.items if proj.title.lower() == repo.name.lower()), 'No description available.').split('- ')[0]}\n"
            f"\\begin{{itemize}}\n"
            + "".join([f"\\item {point.strip()}\n" for point in next((proj.description for proj in linkedin_data.projects.items if proj.title.lower() == repo.name.lower()), 'No description available.').replace("%", "\\%").split('- ')[1:]]) +
            f"\\item \\textbf{{Stars:}} {repo.stargazerCount}\n"
            f"\\end{{itemize}}\n"
            for repo in repositories[:3]
        ])

        languages = set() 
        for repo in repositories:
            for language in repo.languages:
                languages.add(language.name)

        github_languages = ", ".join(languages) if languages else "No languages found"

        final_technical_skills = f"{github_languages}"

        experiences = linkedin_data.position
        certifications = linkedin_data.certifications
        speaks = linkedin_data.languages
        
        def month_number_to_abbr(month_number: int) -> str:
            return calendar.month_abbr[month_number]

        experience_entries = "".join([
            f"\\textbf{{{exp.title}}} \\hfill {month_number_to_abbr(exp.start.month)} {exp.start.year} - "
            f"{f'{month_number_to_abbr(exp.end.month)} {exp.end.year}' if exp.end and exp.end.year != 0 else 'Present'}\\\\\n"
            f"{exp.companyName} \\hfill \\textit{{{exp.location}}}\n"
            f"\n{exp.description.split('- ')[0]}\n"
            f"\\begin{{itemize}}\n"
            + "".join([f"\\item {point.strip()}\n" for point in exp.description.replace("%", "\\%").split('- ')[1:]]) +
            f"\\end{{itemize}}\n"
            for exp in experiences
        ])

        certification_entries = "".join([
            f"\\item {cert.name}\n" for cert in certifications
        ])
        
        speaks_entries = "".join([
            f"\\item {speak.name} ({speak.proficiency.replace('PROFESSIONAL_WORKING', 'Professional').replace('ELEMENTARY', 'Elementary').replace('NATIVE_OR_BILINGUAL', 'Native')})\n" for speak in speaks
        ])

        updated_content = template_content.replace("<REPOSITORIES>", repo_entries)
        updated_content = updated_content.replace("<EXPERIENCES>", experience_entries)
        updated_content = updated_content.replace("<CERTIFICATIONS>", certification_entries)
        updated_content = updated_content.replace("<GITHUB_LANGS>", final_technical_skills)
        updated_content = updated_content.replace("<SPEAKS>", speaks_entries)
        updated_content = updated_content.replace("<SUMMARY>", linkedin_data.summary)

        with open(OUTPUT_FILE, "w") as output_file:
            output_file.write(updated_content)

        print(f"LaTeX file updated: {OUTPUT_FILE}")
    except Exception as e:
        print(f"Error updating LaTeX template: {e}")

query = """
{
  viewer {
    login
    name
    repositories(first: 100, orderBy: {field: STARGAZERS, direction: DESC}) {
      nodes {
        name
        url
        languages(first: 10) {
          nodes {
            name
          }
        }
        stargazerCount
      }
    }
  }
}
"""

if __name__ == "__main__":
    try:
        github_data = fetch_github_data(query)
        linkedin_data = fetch_linkedin_data()
        update_latex_template(github_data, linkedin_data)
    except Exception as e:
        print("Error:", e)
