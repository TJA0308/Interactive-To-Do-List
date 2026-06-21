# Focus Board

Focus Board is a Streamlit task tracker for planning work, tracking progress, and keeping deadlines visible.

## Features

- Add, edit, and delete tasks
- Track status with `Open`, `In Progress`, and `Done`
- Assign priority and due dates
- Search, filter, and sort tasks
- See summary metrics and overdue counts
- Export tasks as CSV
- Save task data locally in `tasks.json`

## Tech Stack

- Python
- Streamlit
- JSON storage for local persistence

## Run Locally

```bash
pip install -r requirements.txt
streamlit run app.py
```

## Deploy on Streamlit

1. Push this repo to GitHub.
2. Create a new app on Streamlit Community Cloud.
3. Connect the GitHub repository.
4. Set the main file path to `app.py`.
5. Deploy.

## Notes

- The app uses `tasks.json` for lightweight local persistence.
- On hosted Streamlit environments, filesystem persistence can be limited, so export CSV if you want a backup of your tasks.
