# Doctor

## Install

### Mac 

```
brew install python
pip install pdm
pdm install
```
### Windows

Install Python https://www.python.org/downloads/windows/

```
pip install pdm
pdm install
```

## Usage

```
pdm run python -m bin.cli
```

Then input the path to your project to analyze. 
For large project it can take couple of minutes

## Use cases

* common - finds known configurations like Dockerfile or CI/CD pipelines and check if there instructions.
* parallents - parallel entities. Finds them in code and in docs. If some are missing, suggests to document

# License 
Business Source License 1.1