import re
import requests
import os
import json
from dotenv import load_dotenv
from models.linkedin import *
from models.github import *
import calendar

load_dotenv()

GITHUB_API_URL = "https://api.github.com/graphql"
GITHUB_TOKEN = os.getenv("TOKEN")

LINKEDIN_API_URL = "https://li-data-scraper.p.rapidapi.com/get-profile-data-by-url"
LINKEDIN_API_KEY = os.getenv("LINKEDIN_API_KEY")
LINKEDIN_PROFILE_URL = os.getenv("LINKEDIN_PROFILE_URL")

TEMPLATE_FILE = "misc/template.tex"
OUTPUT_FILE = "resume.tex"
GITHUB_DATA_FILE = "github_data.json"
LINKEDIN_DATA_FILE = "linkedin_data.json"
local = os.getenv("LOCAL")

def cleanData(data: str) -> str:
    data = re.sub(r'[^\x00-\x7F]+', '', data)
    data = data.replace('\u0000', '')
    return data

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
            data = response.json()
            data = data["data"]
            if local : 
                with open(GITHUB_DATA_FILE, "w") as file:
                    json.dump(data, file)
        else:
            raise Exception(f"Github query failed: {response.status_code}: {response.text}")
    return GithubResponse.parse_obj(data)

def fetch_linkedin_data() -> LinkedinProfile:
    if local and os.path.exists(LINKEDIN_DATA_FILE):
        with open(LINKEDIN_DATA_FILE, "r") as file:
            data = json.load(file)
            print("LinkedIn data from file:")
            print(json.dumps(data.get('projects', {}), indent=2))  # Debug projects specifically
            
    else:
        headers = {
            "x-rapidapi-key": LINKEDIN_API_KEY,
            "x-rapidapi-host": "li-data-scraper.p.rapidapi.com",
        }
        params = {"url": LINKEDIN_PROFILE_URL}
        response = requests.get(LINKEDIN_API_URL, headers=headers, params=params)
        if response.status_code == 200:
            data = response.json()
            print("LinkedIn API response:")
            print(json.dumps(data.get('projects', {}), indent=2))  # Debug projects
            if local:
                with open(LINKEDIN_DATA_FILE, "w") as file:
                    json.dump(data, file)
        else:
            raise Exception(f"LinkedIn fetch failed: {response.status_code}: {response.text}")
    
    print("\nAttempting to parse with Pydantic:")
    print("Projects structure:", type(data.get('projects')), data.get('projects'))
    
    return LinkedinProfile.parse_obj(data)
def update_latex_template(data: GithubResponse, linkedin_data: LinkedinProfile) -> None:
    try:
        with open(TEMPLATE_FILE, "r") as template_file:
            template_content = template_file.read()

        repositories = data.viewer.repositories
        
        def get_project_description(repo_name: str) -> str:
            if not hasattr(linkedin_data, 'projects') or not linkedin_data.projects or not linkedin_data.projects.items:
                return 'No description available.'
                
            matching_project = next(
                (proj for proj in linkedin_data.projects.items 
                 if proj.title.lower() == repo_name.lower()), 
                None
            )
            return matching_project.description if matching_project else 'No description available.'

        repo_entries = "".join([
            f"\\item \\textbf{{\\href{{{repo.url}}}{{{repo.name}}}}} | \\textbf{{{repo.stargazerCount}}} stars\n"
            f"\n{cleanData(get_project_description(repo.name).split('- ')[0])}\n"
            f"\\begin{{itemize}}\n"
            + "".join([
                f"\\item {cleanData(point.strip())}\n" 
                for point in get_project_description(repo.name).replace("%", "\\%").split('- ')[1:]
                if point.strip()  # Only include non-empty points
            ]) +
            f"\\end{{itemize}}\n"
            for repo in repositories[:3]
        ])

        languages = set() 
        for repo in repositories:
            for language in repo.languages:
                languages.add(language.name)

        github_languages = ", ".join(languages) if languages else ""

        experiences = getattr(linkedin_data, 'position', [])
        certifications = getattr(linkedin_data, 'certifications', [])
        speaks = getattr(linkedin_data, 'languages', [])
        
        def month_number_to_abbr(month_number: int) -> str:
            try:
                return calendar.month_abbr[month_number]
            except (IndexError, TypeError):
                return "Unknown"

        experience_entries = "".join([
            f"\\textbf{{{cleanData(exp.title)}}} \\hfill {month_number_to_abbr(exp.start.month)} {exp.start.year} - "
            f"{f'{month_number_to_abbr(exp.end.month)} {exp.end.year}' if exp.end and exp.end.year != 0 else 'Present'}\\\\\n"
            f"{cleanData(exp.companyName)} \\hfill \\textit{{{cleanData(exp.location)}}}\n"
            + (f"\n{cleanData(exp.description.split('- ')[0])}\n"
               f"\\begin{{itemize}}\n"
               + "".join([f"\\item {cleanData(point.strip())}\n" 
                         for point in exp.description.replace("%", "\\%").split('- ')[1:]
                         if point.strip()]) +
               f"\\end{{itemize}}\n"
               if exp.description and "- " in exp.description 
               else f"\n{cleanData(exp.description or 'No description available.')}\n\n")
            for exp in experiences
        ])

        certification_entries = ", ".join([
            f"{cleanData(cert.name)}" for cert in certifications
        ]) or "None"
        
        speaks_entries = ", ".join([
            f"{cleanData(speak.name)} ({cleanData(speak.proficiency.replace('PROFESSIONAL_WORKING', 'Professional').replace('ELEMENTARY', 'Elementary').replace('NATIVE_OR_BILINGUAL', 'Native'))})" 
            for speak in speaks
        ]) or "None"

        updated_content = template_content.replace("<REPOSITORIES>", repo_entries)
        updated_content = updated_content.replace("<EXPERIENCES>", experience_entries)
        updated_content = updated_content.replace("<CERTIFICATIONS>", certification_entries)
        updated_content = updated_content.replace("<GITHUB_LANGS>", github_languages)
        updated_content = updated_content.replace("<SPEAKS>", speaks_entries)
        updated_content = updated_content.replace("<NAME>", f"{getattr(linkedin_data, 'firstName', '')} {getattr(linkedin_data, 'lastName', '')}")
        updated_content = updated_content.replace("<LOCATION>", getattr(data.viewer, 'location', '') or '')
        updated_content = updated_content.replace("<EMAIL>", getattr(data.viewer, 'email', '') or '')
        updated_content = updated_content.replace("<LINKEDIN>", f"linkedin.com/in/{getattr(linkedin_data, 'username', '')}" if getattr(linkedin_data, 'username', '') else '')
        website_url = getattr(data.viewer, 'websiteUrl', '') or ''
        updated_content = updated_content.replace("<URL>", website_url.replace("https://", "").replace("http://", ""))
        updated_content = updated_content.replace("<SUMMARY>", cleanData(getattr(linkedin_data, 'summary', '') or ''))

        with open(OUTPUT_FILE, "w") as output_file:
            output_file.write(cleanData(updated_content))

        print(f"LaTeX file updated: {OUTPUT_FILE}")
    except Exception as e:
        print(f"Error updating LaTeX template: {e}")
        raise e


query = """
{
  viewer {
    login
    name
    location
    websiteUrl
    email
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
        exit(1)