# proofrun

A small harness that tests language models on two kinds of work:

1. **Bug-fix tasks.** The model reads an issue and a repository. The model writes a patch. The harness applies the patch and runs the tests.
2. **Research questions.** The model answers a question. The harness grades the answer against a verified answer.

The harness uses only the Python standard library. Bug-fix tasks can be in any language. The samples use Python and JavaScript.

## Tasks in this repository

| Task | Library | Bug | Source |
|---|---|---|---|
| `py-more-itertools-1153` | more-itertools | `reversed()` fails on an empty `numeric_range` | [pull request 1153](https://github.com/more-itertools/more-itertools/pull/1153) |
| `py-more-itertools-1193` | more-itertools | `interleave_evenly()` fails with no iterables | [pull request 1193](https://github.com/more-itertools/more-itertools/pull/1193) |
| `py-more-itertools-1308` | more-itertools | `bucket()` ignores a falsey validator | [issue 1308](https://github.com/more-itertools/more-itertools/issues/1308) |
| `js-nanoid-618` | nanoid | The command line tool accepts sizes that are not integers | [pull request 618](https://github.com/ai/nanoid/pull/618) |
| `js-nanoid-616` | nanoid | Wrong IDs for a size that is not an integer | [pull request 616](https://github.com/ai/nanoid/pull/616) |
| `py-slugkit-001`, `js-rangekit-001` | samples | Small tasks that show the format | this repository |

Each real task clones the library at the commit before the fix. The tests and the fix come from the library authors. The issue text is a short summary written for this harness.

## Quick start

You need Python 3.10 or later, git, and Node.js 18 or later (for the JavaScript tasks). The real tasks need network access to clone the libraries. The harness works on Linux and Windows.

```bash
# Check that each task is correct
python3 -m proofrun validate

# Run the tests of the harness
python3 -m unittest discover -s tests -t .

# Run all tasks with your model
python3 -m proofrun run --solver command --command "your-model-program" --out runs/first
```

`your-model-program` is any program that reads a prompt from standard input and prints a reply. Use a model command line tool or a short script that calls a model provider.

## How a bug-fix task runs

1. The harness copies the repository into a new work folder. If the task has `repo_url`, the harness clones it and checks out `base_commit`.
2. The harness applies `tests.patch`. This patch adds the tests that describe the bug.
3. The harness runs the `fail_to_pass` commands. They must fail. If one passes, the task is invalid.
4. The harness sends the issue and the source files to the solver. The solver returns a patch.
5. The harness applies the patch and runs `fail_to_pass` and `pass_to_pass`.

| Outcome | Meaning |
|---|---|
| `resolved` | All test commands pass. |
| `tests_still_fail` | The patch applies, but the bug is still there. |
| `broke_passing_tests` | The patch fixes the bug and breaks a test that passed before. |
| `patch_did_not_apply` | git rejects the patch. |
| `empty_patch` | The reply has no patch. |
| `timeout` | A test command did not finish in time. |
| `invalid_task` | The task is incorrect. The model is not at fault. |
| `solver_error` | The model program failed. |

These outcomes are the start of a failure analysis. Sort the runs by outcome, then read the patches in `results.jsonl`.

## How a research question runs

The harness asks the model to end its reply with `ANSWER: <answer>`. The grader reads that line.

| `answer_type` | Rule |
|---|---|
| `text` | Compare after normalization (case, punctuation, accents, articles). `aliases` lists other accepted spellings. The comparison is exact. |
| `number` | Compare numeric values. `tolerance` sets the allowed difference. The default is 0. |
| `date` | Compare calendar dates in many written forms. An expected year accepts a full date in that year. |

Outcomes: `correct`, `incorrect`, `no_answer`, `solver_error`.

## Solvers

| Solver | Use |
|---|---|
| `oracle` | Returns the known correct answer. It proves that a task can be solved. |
| `nop` | Returns nothing. It proves that a task does not pass without work. |
| `command` | Sends the prompt to your program. |

`validate` runs `oracle` and `nop` on each task. A correct task succeeds with `oracle` and does not succeed with `nop`.

## Add a bug-fix task from a real repository

Make a folder in `tasks/bugfix/` with these files:

```
my-task-001/
  task.json     settings (see below)
  issue.md      the text of the issue
  tests.patch   the tests from the fix, without the fix
  gold.patch    the fix, without the tests
```

```json
{
  "id": "my-task-001",
  "language": "python",
  "repo_url": "https://github.com/OWNER/REPO.git",
  "base_commit": "the commit immediately before the fix",
  "image": "python:3.12-slim",
  "install": "pip install -e .",
  "fail_to_pass": ["python -m pytest tests/test_x.py::test_new"],
  "pass_to_pass": ["python -m pytest tests/test_x.py::test_old"],
  "context_files": ["src/pkg/module.py"]
}
```

Find a merged pull request that fixes a bug and adds a test. Divide its diff into `tests.patch` and `gold.patch`. Then run `python3 -m proofrun validate --only my-task-001`.

`context_files` is optional. Without it, the prompt includes all text files up to a size limit. Set it for a large repository. The harness sends the listed files in full.

## Add a research question

Add one line to a `.jsonl` file in `tasks/research/`:

```json
{"id": "q-001", "question": "...", "answer": "...", "answer_type": "text", "aliases": [], "sources": ["link to the primary source"]}
```

The 3 questions in `samples.jsonl` show the format only. They are not hard questions.

## Other options

- `--repeat 10` runs each task 10 times. Use it to measure how frequently a model fails.
- `--kind bugfix` or `--kind research` selects one task kind.
- `--only ID ...` selects tasks by id.
- `--keep` keeps the work folders for inspection.
- `--backend docker` runs the test commands in the Docker image of the task, with no network.

## Limits

- The `local` backend runs model patches and test commands on your machine. Use it only for code that you trust. Use `--backend docker` for other code.
- The `docker` backend stops with a clear error if Docker is not available. The author did not complete a full Docker run yet.
- With the `docker` backend, the `install` command also runs without network. Use an image that already contains the dependencies.
- The model sees the source files in one prompt. The harness does not give the model tools to search the repository or the web.
- The text grader is exact after normalization. Add each accepted spelling to `aliases`.
