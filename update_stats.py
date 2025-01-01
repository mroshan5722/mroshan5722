import datetime
from dateutil import relativedelta
import requests
import os
from xml.dom import minidom

# GitHub API headers
HEADERS = {'authorization': 'token ' + os.environ['ACCESS_TOKEN']}
USER_NAME = os.environ['USER_NAME']


def get_age(birthday):
    """
    Calculate the age since the given birthday.
    """
    diff = relativedelta.relativedelta(datetime.datetime.today(), birthday)
    return '{} years, {} months, {} days'.format(diff.years, diff.months, diff.days)


def fetch_github_data():
    """
    Fetch data for repositories, contributions, commits, stars, followers, and LOC from GitHub API.
    """
    # GraphQL query templates
    repo_query = '''
    query($login: String!) {
        user(login: $login) {
            repositories {
                totalCount
            }
        }
    }'''

    star_query = '''
    query($login: String!) {
        user(login: $login) {
            repositories {
                edges {
                    node {
                        stargazers {
                            totalCount
                        }
                    }
                }
            }
        }
    }'''

    commit_query = '''
    query($login: String!) {
        user(login: $login) {
            contributionsCollection {
                totalCommitContributions
            }
        }
    }'''

    follower_query = '''
    query($login: String!) {
        user(login: $login) {
            followers {
                totalCount
            }
        }
    }'''

    loc_query = '''
    query($login: String!) {
        user(login: $login) {
            repositories(first: 100) {
                edges {
                    node {
                        name
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
            }
        }
    }'''

    # Send GraphQL requests
    def run_query(query, variables):
        response = requests.post('https://api.github.com/graphql', json={'query': query, 'variables': variables}, headers=HEADERS)
        if response.status_code != 200:
            raise Exception(f"GitHub API request failed: {response.status_code} {response.text}")
        return response.json()

    # Fetch data
    repo_data = run_query(repo_query, {'login': USER_NAME})['data']['user']['repositories']['totalCount']
    star_data = sum(edge['node']['stargazers']['totalCount'] for edge in
                    run_query(star_query, {'login': USER_NAME})['data']['user']['repositories']['edges'])
    commit_data = run_query(commit_query, {'login': USER_NAME})['data']['user']['contributionsCollection']['totalCommitContributions']
    follower_data = run_query(follower_query, {'login': USER_NAME})['data']['user']['followers']['totalCount']

    # LOC data
    loc_data = run_query(loc_query, {'login': USER_NAME})['data']['user']['repositories']['edges']
    loc_added, loc_removed, loc_total = 0, 0, 0

    for repo in loc_data:
        try:
            history = repo['node']['defaultBranchRef']['target']['history']
            loc_total += history['totalCount']
        except (TypeError, KeyError):
            continue

    return repo_data, commit_data, star_data, follower_data, loc_total, loc_added, loc_removed


def update_svg(filename, age, repo_count, contrib_count, commit_count, star_count, follower_count, loc_total, loc_added, loc_removed):
    """
    Update the SVG file with the provided values.
    """
    svg = minidom.parse(filename)
    tspan = svg.getElementsByTagName('tspan')

    # Update the specific tspans with the new data
    tspan[43].firstChild.data = age  # Update age
    tspan[68].firstChild.data = str(repo_count)  # Repositories
    tspan[70].firstChild.data = str(contrib_count)  # Contributions
    tspan[72].firstChild.data = str(commit_count)  # Commits
    tspan[74].firstChild.data = str(star_count)  # Stars
    tspan[76].firstChild.data = str(follower_count)  # Followers
    tspan[78].firstChild.data = str(loc_total)  # Total LOC
    tspan[79].firstChild.data = f"{loc_added}++"  # LOC Added
    tspan[80].firstChild.data = f"{loc_removed}--"  # LOC Removed

    # Save the updated SVG
    with open(filename, 'w', encoding='utf-8') as file:
        file.write(svg.toxml())


if __name__ == '__main__':
    # User-defined birthday
    birthday = datetime.datetime(2003, 6, 13)

    # Fetch data
    age = get_age(birthday)
    repo_count, commit_count, star_count, follower_count, loc_total, loc_added, loc_removed = fetch_github_data()

    # Update SVG files
    update_svg('dark.svg', age, repo_count, repo_count, commit_count, star_count, follower_count, loc_total, loc_added, loc_removed)
    update_svg('light.svg', age, repo_count, repo_count, commit_count, star_count, follower_count, loc_total, loc_added, loc_removed)
