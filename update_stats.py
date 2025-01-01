import datetime
from dateutil import relativedelta
import requests
import os
from xml.dom import minidom

# GitHub API headers
HEADERS = {'Authorization': f'token {os.environ["ACCESS_TOKEN"]}'}
USER_NAME = os.environ['USER_NAME']

def calculate_age(birthday):
    """
    Calculate time since birthday in years, months, and days.
    """
    today = datetime.date.today()
    diff = relativedelta.relativedelta(today, birthday)
    return f"{diff.years} year{'s' if diff.years != 1 else ''}, {diff.months} month{'s' if diff.months != 1 else ''}, {diff.days} day{'s' if diff.days != 1 else ''}"

def fetch_github_data(query, variables):
    """
    Fetch data from GitHub GraphQL API.
    """
    response = requests.post(
        'https://api.github.com/graphql',
        json={'query': query, 'variables': variables},
        headers=HEADERS
    )
    response.raise_for_status()
    return response.json()

def get_repositories():
    """
    Fetch all repositories owned by the user.
    """
    query = '''
    query($login: String!, $cursor: String) {
        user(login: $login) {
            repositories(first: 100, after: $cursor, ownerAffiliations: OWNER) {
                edges {
                    node {
                        name
                        nameWithOwner
                        defaultBranchRef {
                            target {
                                ... on Commit {
                                    history {
                                        totalCount
                                    }
                                }
                            }
                        }
                    }
                }
                pageInfo {
                    endCursor
                    hasNextPage
                }
            }
        }
    }
    '''
    variables = {'login': USER_NAME, 'cursor': None}
    repositories = []
    while True:
        data = fetch_github_data(query, variables)
        edges = data['data']['user']['repositories']['edges']
        repositories.extend(edges)
        if not data['data']['user']['repositories']['pageInfo']['hasNextPage']:
            break
        variables['cursor'] = data['data']['user']['repositories']['pageInfo']['endCursor']
    return repositories

def calculate_loc(repository):
    """
    Calculate the lines of code added and removed for a given repository.
    """
    owner, name = repository['node']['nameWithOwner'].split('/')
    query = '''
    query($owner: String!, $name: String!) {
        repository(owner: $owner, name: $name) {
            defaultBranchRef {
                target {
                    ... on Commit {
                        history(first: 100) {
                            edges {
                                node {
                                    additions
                                    deletions
                                }
                            }
                        }
                    }
                }
            }
        }
    }
    '''
    variables = {'owner': owner, 'name': name}
    additions = 0
    deletions = 0
    data = fetch_github_data(query, variables)
    edges = data['data']['repository']['defaultBranchRef']['target']['history']['edges']
    for edge in edges:
        additions += edge['node']['additions']
        deletions += edge['node']['deletions']
    return additions, deletions

def get_total_loc(repositories):
    """
    Get the total lines of code added and removed across all repositories.
    """
    total_additions = 0
    total_deletions = 0
    for repo in repositories:
        additions, deletions = calculate_loc(repo)
        total_additions += additions
        total_deletions += deletions
    return total_additions, total_deletions, total_additions - total_deletions

def get_github_stats():
    """
    Get GitHub stats: repositories, commits, stars, followers.
    """
    query = '''
    query($login: String!) {
        user(login: $login) {
            repositories(ownerAffiliations: OWNER, isFork: false) { totalCount }
            starredRepositories { totalCount }
            followers { totalCount }
            contributionsCollection {
                contributionCalendar { totalContributions }
            }
        }
    }
    '''
    variables = {'login': USER_NAME}
    data = fetch_github_data(query, variables)['data']['user']
    repos = data['repositories']['totalCount']
    stars = data['starredRepositories']['totalCount']
    followers = data['followers']['totalCount']
    commits = data['contributionsCollection']['contributionCalendar']['totalContributions']
    return repos, stars, followers, commits

def update_svg(filename, age, repos, contributed, commits, stars, followers, loc_added, loc_deleted, loc_total):
    """
    Update the SVG file with the dynamic stats and age information.
    """
    svg = minidom.parse(filename)
    tspan = svg.getElementsByTagName('tspan')

    # Update placeholders
    tspan[43].firstChild.data = f"Uptime: {age}"  # Age
    tspan[68].firstChild.data = f"Repos: {repos} {{Contributed: {contributed}}}"  # Repos
    tspan[72].firstChild.data = f"Commits: {commits}"  # Commits
    tspan[74].firstChild.data = f"Stars: {stars}"  # Stars
    tspan[76].firstChild.data = f"Followers: {followers}"  # Followers
    tspan[78].firstChild.data = f"Lines of Code: {loc_total} ({loc_added}++, {loc_deleted}--)"  # LOC

    # Save updated file
    with open(filename, 'w', encoding='utf-8') as file:
        file.write(svg.toxml())
        
if __name__ == "__main__":
    # Define your birthday (Year, Month, Day)
    birthday = datetime.date(2003, 6, 13)

    # Calculate age
    age = calculate_age(birthday)

    # Fetch repositories and calculate LOC
    repositories = get_repositories()
    loc_added, loc_deleted, loc_total = get_total_loc(repositories)

    # Fetch GitHub stats
    repos, stars, followers, commits = get_github_stats()

    # Update SVG files
    update_svg('dark.svg', age, repos, 133, commits, stars, followers, loc_added, loc_deleted, loc_total)
    update_svg('light.svg', age, repos, 133, commits, stars, followers, loc_added, loc_deleted, loc_total)

    print("SVG files updated successfully!")
