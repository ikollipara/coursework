# Coursework

A command-line auto-grader built for Concordia University, Nebraska.

## Usage

Coursework includes 3 different utilities:
1. `coursework`
2. `coursework-admin`
3. `coursework-score`

### `coursework`

`coursework` is the utility used by students.
It features 3 commands:
1. `coursework list`
2. `coursework detail COURSE ASSIGNMENT`
3. `coursework submit COURSE ASSIGNMENT [FILES]`


The key command is `submit`. This runs the given assignment's test script, presenting the output to the user
in a prettified format. In addition, it creates and saves the directories for student work.

### `coursework-admin`

`coursework-admin` is the utility used by administrators and instructors.
It features 2 commands:
1. `edit`
2. `report COURSE ASSIGNMENT`

`edit` allows the instructor to edit the configuration for coursework, which is stored at `$COURSEWORK_CONFIG` (defaults to `/usr/local/etc/coursework.toml`).
If the edits result in an improperly configured setup, you will be forced to resolve the issue before final edits can be saved.

`report` will generate a pdf report for all the given assignments in the instructor's `coursework` directory.

## Configuration

Coursework is configured from a toml file, conventionally named `coursework.toml`.
It consists of 3 kinds of blocks:
1. `coursework` Top-level configuration details
2. `courses.*` Course configuration
3. `assignments.*` Assignment configuration

`coursework` block contains the following attributes:
- `admins`: `list[str]` The list of admin users. Used to determine who can use `coursework-admin`.
- `admin_group`: `str` The group used when changing the ownership of generated files. This matters for integrity.
- `submission`: `Optional[str]` An optional value for where submitted files should go. This is a template string with 3 variables: student, course, and assignment.
- `collection`: `Optional[str]` An optional value for where collected reports should go. This is a template string with 3 variables: instructor, course, assignment.

`courses.*` blocks contain the following:
- `instructors`: `list[str]` A list of instructor accounts.
- `students`: `list[str]` A list of student accounts. These students will see assignments for the given course.
- `assignments`: `list[str]` A list of assignment names. These are shown for the course.

`assignments.*` blocks contain the following:
- `description`: `str` A markdown string that displays a short description of the assignment.
- `due_date`: `str` A date string of the form: "YYYY-MM-DD 24:00". This is the due date for a particular assignment.
- `total_points`: `int` A positive integer representing the total possible points for an assignment.
- `test`: `str` A 2 part string, separated by ":" that describes the test runner and test script. (Example: `cmd:/home/ian/test_script.sh`). These scripts **must** be written as absolute paths. Accepted runner values are: `cmd` and `py`.

## Deployment Checklist

```
# Local
uv build
scp dist/coursework-0.0.1-py3-none-any.whl ian.kollipara@csa2.cune.edu:~/coursework-0.0.1-py3-none-any.whl
scp dist/coursework ian.kollipara@csa2.cune.edu:~/coursework-bin
scp dist/coursework-admin ian.kollipara@csa2.cune.edu:~/coursework-admin-bin

# On CSA
sudo pip install coursework-0.0.1-py3-none-any.whl --break-system-packages --force-reinstall
sudo mv ~/coursework-bin /usr/local/bin/coursework
sudo mv ~/coursework-admin-bin /usr/local/bin/coursework-admin
sudo chown root:root /usr/local/bin/coursework-score
sudo chown root:root /usr/local/bin/coursework-admin
sudo chown root:root /usr/local/bin/coursework
sudo chmod u+s /usr/local/bin/coursework
sudo chmod u+s /usr/local/bin/coursework-admin
sudo chmod u+s /usr/local/bin/coursework-score
```
