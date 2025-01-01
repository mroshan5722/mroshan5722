import datetime
from dateutil import relativedelta
import requests
import os
from xml.dom import minidom

# Access environment variables for authentication
HEADERS = {'Authorization': f'token {os.environ["ACCESS_TOKEN"]}'}
USER_NAME = os.environ['USER_NAME']

def daily_readme(birthday):
    """
    Calculate the time since the user's birthday (e.g., 'XX years, XX months, XX days').
    """
    diff = relativedelta.relativedelta(datetime.datetime.today(), birthday)
    return '{} year{}, {} month{}, {} day{}'.format(
        diff.years, 's' if diff.years != 1 else '',
        diff.months, 's' if diff.months != 1 else '',
        diff.days, 's' if diff.days != 1 else ''
    )

def fetch_github_data(query, variables):
    """
    Perform a GraphQL request to the GitHub API.
    """
    response = requests.post(
        'https://api.github.com/graphql',
        json={'query': query, 'variables': variables},
        headers=HEADERS
    )
    if response.status_code != 200:
        raise Exception(f"GitHub API request failed: {response.status_code} - {response.text}")
    return response.json()

def get_total_commits():
    """
    Fetch the total number of commits for the user.
    """
    query = '''
    query($login: String!) {
        user(login: $login) {
            contributionsCollection {
                contributionCalendar {
                    totalContributions
                }
            }
        }
    }
    '''
    variables = {'login': USER_NAME}
    data = fetch_github_data(query, variables)
    return data['data']['user']['contributionsCollection']['contributionCalendar']['totalContributions']

def get_total_repos_and_stars():
    """
    Fetch the total number of repositories and stars for the user.
    """
    query = '''
    query($login: String!) {
        user(login: $login) {
            repositories(ownerAffiliations: OWNER, isFork: false) {
                totalCount
            }
            starredRepositories {
                totalCount
            }
        }
    }
    '''
    variables = {'login': USER_NAME}
    data = fetch_github_data(query, variables)
    repos = data['data']['user']['repositories']['totalCount']
    stars = data['data']['user']['starredRepositories']['totalCount']
    return repos, stars

def get_total_followers():
    """
    Fetch the total number of followers for the user.
    """
    query = '''
    query($login: String!) {
        user(login: $login) {
            followers {
                totalCount
            }
        }
    }
    '''
    variables = {'login': USER_NAME}
    data = fetch_github_data(query, variables)
    return data['data']['user']['followers']['totalCount']

def update_svg(filename, age, commits, repos, stars, followers):
    """
    Update placeholders in the SVG file with dynamic data.
    """
    svg = minidom.parse(filename)
    tspan = svg.getElementsByTagName('tspan')

    # Update placeholders with dynamic data
    tspan[0].firstChild.data = f"Age: {age}"
    tspan[1].firstChild.data = f"Total Commits: {commits}"
    tspan[2].firstChild.data = f"Total Repositories: {repos}"
    tspan[3].firstChild.data = f"Total Stars: {stars}"
    tspan[4].firstChild.data = f"Total Followers: {followers}"

    # Save the updated SVG
    with open(filename, 'w', encoding='utf-8') as file:
        file.write(svg.toxml())

if __name__ == '__main__':
    # Define the user's birthday for age calculation
    birthday = datetime.datetime(2000, 1, 1)  # Replace with your birthday

    # Fetch dynamic data
    age = daily_readme(birthday)
    commits = get_total_commits()
    repos, stars = get_total_repos_and_stars()
    followers = get_total_followers()

    # Update SVG files
    update_svg('dark.svg', age, commits, repos, stars, followers)
    update_svg('light.svg', age, commits, repos, stars, followers)

    print("SVG files updated successfully.")
