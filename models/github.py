from pydantic import BaseModel
from typing import List, Optional

class Language(BaseModel):
    name: str

class Repository(BaseModel):
    name: str
    url: str
    stargazerCount: int
    languages: List[Language]
    description: Optional[str] = None  # Add this line to include the description field
    
    @classmethod
    def parse_obj(cls, obj: dict):
        # Extract the list of languages from the 'nodes' key
        obj['languages'] = obj['languages']['nodes']
        return super().parse_obj(obj)
    
class Viewer(BaseModel):
    login: str
    name: str
    repositories: List[Repository]

class GithubResponse(BaseModel):
    viewer: Viewer
    
    @classmethod
    def parse_obj(cls, obj: dict):
        # Extract the list of repositories from the 'nodes' key
        obj['viewer']['repositories'] = [Repository.parse_obj(repo) for repo in obj['viewer']['repositories']['nodes']]
        return super().parse_obj(obj)