# frontend/main.py
import streamlit as st
import requests
import json
import os
from datetime import datetime # Import datetime for date handling

# --- Configuration ---
# Get the FastAPI backend URL from an environment variable.
# For local Gitpod development, this will point to your local FastAPI in Gitpod.
# For Streamlit Cloud deployment, you will set this env var there.
FASTAPI_BACKEND_URL = os.getenv("FASTAPI_BACKEND_URL", "http://localhost:8000") # Default for local
# Fallback if env var not set (e.g. for very basic local run without .env)
if not FASTAPI_BACKEND_URL:
    st.error("FASTAPI_BACKEND_URL environment variable is not set. Please configure it.")
    st.stop()


# --- API Helper Functions ---
def register_user(username, email, password):
    try:
        response = requests.post(
            f"{FASTAPI_BACKEND_URL}/users/",
            json={"username": username, "email": email, "password": password}
        )
        response.raise_for_status() # Raise an exception for HTTP errors (4xx or 5xx)
        return response.json()
    except requests.exceptions.HTTPError as e:
        st.error(f"Registration failed: {e.response.json().get('detail', 'Unknown error')}")
        return None
    except requests.exceptions.ConnectionError:
        st.error("Could not connect to the backend API. Please ensure the backend is running.")
        return None

def login_user(username, password):
    try:
        # FastAPI's /token endpoint expects x-www-form-urlencoded data
        response = requests.post(
            f"{FASTAPI_BACKEND_URL}/token",
            data={"username": username, "password": password}
        )
        response.raise_for_status()
        return response.json()
    except requests.exceptions.HTTPError as e:
        st.error(f"Login failed: {e.response.json().get('detail', 'Incorrect username or password')}")
        return None
    except requests.exceptions.ConnectionError:
        st.error("Could not connect to the backend API. Please ensure the backend is running.")
        return None

def get_headers():
    # Get token from session state if available
    token = st.session_state.get("access_token")
    if token:
        return {"Authorization": f"Bearer {token}"}
    return {}

def get_current_user_info():
    headers = get_headers()
    if not headers:
        return None
    try:
        response = requests.get(f"{FASTAPI_BACKEND_URL}/users/me/", headers=headers)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.HTTPError as e:
        if e.response.status_code == 401:
            st.session_state["logged_in"] = False
            st.session_state["access_token"] = None
            st.error("Session expired. Please log in again.")
            st.experimental_rerun()
        else:
            st.error(f"Failed to fetch user info: {e.response.json().get('detail', 'Unknown error')}")
        return None
    except requests.exceptions.ConnectionError:
        st.error("Could not connect to the backend API. Please ensure the backend is running.")
        return None

def get_users(): # New function to get all users for task assignment dropdown
    headers = get_headers()
    if not headers:
        return []
    try:
        response = requests.get(f"{FASTAPI_BACKEND_URL}/users/", headers=headers)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.HTTPError as e:
        st.error(f"Failed to fetch users: {e.response.json().get('detail', 'Unknown error')}")
        return []
    except requests.exceptions.ConnectionError:
        st.error("Could not connect to the backend API. Please ensure the backend is running.")
        return []


def get_projects():
    headers = get_headers()
    if not headers:
        return []
    try:
        response = requests.get(f"{FASTAPI_BACKEND_URL}/projects/", headers=headers)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.HTTPError as e:
        st.error(f"Failed to fetch projects: {e.response.json().get('detail', 'Unknown error')}")
        return []
    except requests.exceptions.ConnectionError:
        st.error("Could not connect to the backend API. Please ensure the backend is running.")
        return []

def create_project(name, description):
    headers = get_headers()
    if not headers:
        return None
    try:
        response = requests.post(
            f"{FASTAPI_BACKEND_URL}/projects/",
            json={"name": name, "description": description},
            headers=headers
        )
        response.raise_for_status()
        return response.json()
    except requests.exceptions.HTTPError as e:
        st.error(f"Failed to create project: {e.response.json().get('detail', 'Unknown error')}")
        return None
    except requests.exceptions.ConnectionError:
        st.error("Could not connect to the backend API. Please ensure the backend is running.")
        return None

def get_tasks(project_id=None):
    headers = get_headers()
    if not headers:
        return []
    try:
        if project_id:
            response = requests.get(f"{FASTAPI_BACKEND_URL}/tasks/project/{project_id}", headers=headers)
        else:
            response = requests.get(f"{FASTAPI_BACKEND_URL}/tasks/", headers=headers)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.HTTPError as e:
        st.error(f"Failed to fetch tasks: {e.response.json().get('detail', 'Unknown error')}")
        return []
    except requests.exceptions.ConnectionError:
        st.error("Could not connect to the backend API. Please ensure the backend is running.")
        return []

def create_task(title, description, status, due_date, project_id, assigned_to):
    headers = get_headers()
    if not headers:
        return None
    payload = {
        "title": title,
        "description": description,
        "status": status,
        "project_id": project_id
    }
    if due_date:
        payload["due_date"] = str(due_date) # Convert date object to string for API
    if assigned_to:
        payload["assigned_to"] = assigned_to

    try:
        response = requests.post(
            f"{FASTAPI_BACKEND_URL}/tasks/",
            json=payload,
            headers=headers
        )
        response.raise_for_status()
        return response.json()
    except requests.exceptions.HTTPError as e:
        st.error(f"Failed to create task: {e.response.json().get('detail', 'Unknown error')}")
        return None
    except requests.exceptions.ConnectionError:
        st.error("Could not connect to the backend API. Please ensure the backend is running.")
        return None

def update_task(task_id, updates):
    headers = get_headers()
    if not headers:
        return None
    if "due_date" in updates and updates["due_date"]:
         updates["due_date"] = str(updates["due_date"]) # Convert date object to string
    try:
        response = requests.put(
            f"{FASTAPI_BACKEND_URL}/tasks/{task_id}",
            json=updates,
            headers=headers
        )
        response.raise_for_status()
        return response.json()
    except requests.exceptions.HTTPError as e:
        st.error(f"Failed to update task: {e.response.json().get('detail', 'Unknown error')}")
        return None
    except requests.exceptions.ConnectionError:
        st.error("Could not connect to the backend API. Please ensure the backend is running.")
        return None

def delete_task(task_id):
    headers = get_headers()
    if not headers:
        return False
    try:
        response = requests.delete(f"{FASTAPI_BACKEND_URL}/tasks/{task_id}", headers=headers)
        response.raise_for_status() # Expects 204 No Content
        return True
    except requests.exceptions.HTTPError as e:
        st.error(f"Failed to delete task: {e.response.json().get('detail', 'Unknown error')}")
        return False
    except requests.exceptions.ConnectionError:
        st.error("Could not connect to the backend API. Please ensure the backend is running.")
        return False

# --- Streamlit UI Components ---

def show_registration_page():
    st.subheader("Register New Account")
    with st.form("registration_form"):
        new_username = st.text_input("Username", key="reg_username")
        new_email = st.text_input("Email", key="reg_email")
        new_password = st.text_input("Password", type="password", key="reg_password")
        submit_reg = st.form_submit_button("Register")

        if submit_reg:
            if new_username and new_email and new_password:
                user_data = register_user(new_username, new_email, new_password)
                if user_data:
                    st.success(f"User '{new_username}' registered successfully! Please log in.")
            else:
                st.warning("Please fill in all registration fields.")

def show_login_page():
    st.subheader("Login")
    with st.form("login_form"):
        username = st.text_input("Username", key="login_username")
        password = st.text_input("Password", type="password", key="login_password")
        submit_login = st.form_submit_button("Login")

        if submit_login:
            if username and password:
                token_data = login_user(username, password)
                if token_data:
                    st.session_state["access_token"] = token_data["access_token"]
                    st.session_state["logged_in"] = True
                    st.success("Logged in successfully!")
                    st.experimental_rerun() # Rerun to switch to main app
            else:
                st.warning("Please enter both username and password.")

def logout():
    st.session_state["logged_in"] = False
    st.session_state["access_token"] = None
    st.success("You have been logged out.")
    st.experimental_rerun() # Rerun to show login/register

def show_main_app():
    st.sidebar.title("Navigation")
    app_mode = st.sidebar.radio("Go to", ["Projects Overview", "All Tasks (Kanban)"])

    st.sidebar.markdown("---")
    st.sidebar.button("Logout", on_click=logout)

    current_user = get_current_user_info()
    if current_user:
        st.sidebar.write(f"Logged in as: **{current_user['username']}**")
    else:
        st.sidebar.warning("Could not fetch user info.")
        logout() # Force logout if user info can't be fetched

    if app_mode == "Projects Overview":
        show_projects_overview()
    elif app_mode == "All Tasks (Kanban)":
        show_all_tasks_kanban()

def show_projects_overview():
    st.title("Project Management Dashboard")
    st.subheader("Your Projects")

    projects = get_projects()
    if not projects:
        st.info("No projects found. Create one below!")

    # Display projects
    cols = st.columns(2) # Two columns for layout
    col_idx = 0

    for project in projects:
        with cols[col_idx % 2]:
            with st.expander(f"**{project['name']}** (ID: {project['id']})"):
                st.write(f"**Description:** {project['description']}")
                st.write(f"**Created By:** {project['creator']['username']}")
                st.write(f"**Created On:** {project['created_at'].split('T')[0]}") # Show date only

                # Tasks for this project
                st.subheader(f"Tasks for {project['name']}")
                # Fetch all tasks and filter them by project_id here in frontend for simplicity
                # For very large number of tasks, it's better to fetch by project_id from backend if possible
                all_tasks_for_filter = get_tasks() # Fetch all tasks to filter
                project_tasks = [task for task in all_tasks_for_filter if task['project_id'] == project['id']]
                
                if project_tasks:
                    for task in project_tasks:
                        status_color = "green" if task['status'] == "Done" else ("orange" if task['status'] == "In Progress" else "red")
                        st.markdown(f"**[{task['status']}]** <span style='color:{status_color}'>{task['title']}</span>", unsafe_allow_html=True)
                        st.write(f"Assigned to: {task['assignee']['username'] if task['assignee'] else 'Unassigned'}")
                        if task['due_date']:
                            st.write(f"Due: {task['due_date']}")
                        
                        # Use a unique key for the expander for editing
                        if st.checkbox(f"Edit Task {task['id']}", key=f"proj_edit_task_toggle_{task['id']}"):
                            with st.expander(f"Edit {task['title']}", expanded=True):
                                # Pass all users for the assignee dropdown within the edit form
                                edit_task_form(task, get_users()) 
                                if st.button(f"Close Edit Form {task['id']}", key=f"proj_close_edit_form_{task['id']}"):
                                    st.experimental_rerun() # Just rerun to close the form
                                    
                        if st.button(f"Delete Task {task['id']}", key=f"proj_delete_task_btn_{task['id']}"):
                            # Add a simple confirmation
                            if st.warning(f"Are you sure you want to delete '{task['title']}'?"):
                                if st.button(f"Confirm Delete Task {task['id']}", key=f"proj_confirm_delete_task_btn_{task['id']}"):
                                    if delete_task(task['id']):
                                        st.success("Task deleted.")
                                        st.experimental_rerun()
                                    else:
                                        st.error("Failed to delete task.")
                        st.markdown("---")
                else:
                    st.info("No tasks for this project yet.")
        col_idx += 1
        st.markdown("<br>", unsafe_allow_html=True) # Small gap between cards

    st.markdown("---")
    st.subheader("Create New Project")
    with st.form("new_project_form"):
        project_name = st.text_input("Project Name")
        project_description = st.text_area("Project Description")
        submit_project = st.form_submit_button("Create Project")

        if submit_project:
            if project_name:
                new_proj = create_project(project_name, project_description)
                if new_proj:
                    st.success(f"Project '{new_proj['name']}' created successfully!")
                    st.experimental_rerun()
            else:
                st.warning("Project name cannot be empty.")

    st.subheader("Create New Task")
    with st.form("new_task_form"):
        task_title = st.text_input("Task Title")
        task_description = st.text_area("Task Description")
        task_status = st.selectbox("Status", ["To Do", "In Progress", "Done", "Blocked"])
        task_due_date = st.date_input("Due Date (Optional)", value=None)

        all_projects = get_projects()
        project_options = {p['name']: p['id'] for p in all_projects}
        
        # Handle case where no projects exist yet
        if not project_options:
            st.warning("No projects available. Please create a project first before creating tasks.")
            task_project_id = None
        else:
            selected_project_name = st.selectbox("Assign to Project", list(project_options.keys()))
            task_project_id = project_options.get(selected_project_name)


        all_users = get_users() # Assuming this fetches all users from backend
        user_options = {user['username']: user['id'] for user in all_users}
        selected_assigned_user_name = st.selectbox("Assign to User (Optional)", ["Unassigned"] + list(user_options.keys()))
        task_assigned_to_id = user_options.get(selected_assigned_user_name) if selected_assigned_user_name != "Unassigned" else None

        submit_task = st.form_submit_button("Create Task")

        if submit_task:
            if task_title and task_project_id:
                new_task = create_task(
                    task_title, task_description, task_status,
                    task_due_date, task_project_id, task_assigned_to_id
                )
                if new_task:
                    st.success(f"Task '{new_task['title']}' created successfully!")
                    st.experimental_rerun()
            else:
                st.warning("Task title and Project assignment are required.")

def edit_task_form(task_data, all_users_data):
    # Fetch all users for assignment dropdown (passed as all_users_data)
    user_options = {user['username']: user['id'] for user in all_users_data}
    current_assignee_name = next((u['username'] for u in all_users_data if u['id'] == task_data['assigned_to']), "Unassigned")

    with st.form(f"edit_task_form_{task_data['id']}", clear_on_submit=False): # Unique key for each form
        edited_title = st.text_input("Title", value=task_data['title'], key=f"edit_title_{task_data['id']}")
        edited_description = st.text_area("Description", value=task_data['description'], key=f"edit_desc_{task_data['id']}")
        edited_status = st.selectbox("Status", ["To Do", "In Progress", "Done", "Blocked"], index=["To Do", "In Progress", "Done", "Blocked"].index(task_data['status']), key=f"edit_status_{task_data['id']}")
        
        initial_date_value = None
        if task_data['due_date']:
            try:
                # Ensure date format is correct for datetime.strptime
                initial_date_value = datetime.strptime(task_data['due_date'].split('T')[0], "%Y-%m-%d").date()
            except ValueError:
                pass # Keep as None if date format is bad
        edited_due_date = st.date_input("Due Date (Optional)", value=initial_date_value, key=f"edit_duedate_{task_data['id']}")

        edited_assigned_user_name = st.selectbox("Assign to User (Optional)", ["Unassigned"] + list(user_options.keys()), index=(list(user_options.keys()).index(current_assignee_name) + 1 if current_assignee_name != "Unassigned" else 0), key=f"edit_assignee_{task_data['id']}")
        edited_assigned_to_id = user_options.get(edited_assigned_user_name) if edited_assigned_user_name != "Unassigned" else None

        submit_edit = st.form_submit_button("Update Task")

        if submit_edit:
            updates = {}
            if edited_title != task_data['title']: updates['title'] = edited_title
            if edited_description != task_data['description']: updates['description'] = edited_description
            if edited_status != task_data['status']: updates['status'] = edited_status
            
            # Date handling: check if date actually changed or if it was cleared/set
            if edited_due_date != initial_date_value: 
                updates['due_date'] = edited_due_date
            
            # Handle assigned_to logic carefully: if changed, or if was assigned and now unassigned, or vice-versa
            if edited_assigned_to_id != task_data['assigned_to']: 
                updates['assigned_to'] = edited_assigned_to_id

            if updates:
                updated_task = update_task(task_data['id'], updates)
                if updated_task:
                    st.success(f"Task '{updated_task['title']}' updated successfully!")
                    st.experimental_rerun()
            else:
                st.info("No changes to update.")


def show_all_tasks_kanban():
    st.title("All Tasks (Kanban Board)")
    st.markdown("This Kanban-like display allows you to visualize and update task statuses. Drag and drop is not directly supported in Streamlit, but you can update statuses using the dropdowns.")

    all_tasks = get_tasks()
    all_users = get_users() # Fetch all users once for assignment dropdowns
    all_projects = get_projects() # Fetch all projects once

    # Create dictionaries for quick lookups
    user_map = {user['id']: user['username'] for user in all_users}
    project_map = {project['id']: project['name'] for project in all_projects}

    # Define the order of Kanban columns
    status_order = ["To Do", "In Progress", "Done", "Blocked"] 

    # Group tasks by status
    tasks_by_status = {status: [] for status in status_order}
    for task in all_tasks:
        if task['status'] in tasks_by_status:
            tasks_by_status[task['status']].append(task)
        else:
            # Handle unexpected statuses by putting them in 'To Do' or similar
            tasks_by_status["To Do"].append(task) 

    # Display columns using Streamlit's columns layout
    cols = st.columns(len(status_order)) 

    for i, status in enumerate(status_order):
        with cols[i]:
            st.subheader(f"{status} ({len(tasks_by_status[status])})")
            st.markdown("---") # Visual separator for columns

            if not tasks_by_status[status]:
                st.info("No tasks here.")
            
            for task in tasks_by_status[status]:
                card_title = f"{task['title']}"
                card_description = task['description'] if task['description'] else "No description"
                assignee_name = user_map.get(task['assigned_to'], "Unassigned")
                project_name = project_map.get(task['project_id'], "Unknown Project")
                due_date_display = f"Due: {task['due_date']}" if task['due_date'] else ""

                # Task Card (using Streamlit components for visual grouping)
                with st.container(border=True): # New in Streamlit 1.25.0 for bordered containers
                    st.markdown(f"**{card_title}**")
                    st.caption(f"Project: {project_name}")
                    st.write(card_description)
                    st.write(f"Assigned to: {assignee_name}")
                    if due_date_display:
                        st.write(due_date_display)

                    # Status update dropdown
                    # Ensure index is within bounds
                    try:
                        current_status_index = status_order.index(task['status'])
                    except ValueError:
                        current_status_index = 0 # Default to 'To Do' if status is unrecognized

                    new_status = st.selectbox(
                        "Change Status",
                        status_order,
                        index=current_status_index,
                        key=f"status_select_{task['id']}" # Unique key for each selectbox
                    )
                    if new_status != task['status']:
                        if update_task(task['id'], {"status": new_status}):
                            st.success(f"Task '{task['title']}' moved to '{new_status}'")
                            st.experimental_rerun() # Rerun to update Kanban view

                    # Use session state to control expander visibility for edit form
                    if f"show_edit_form_{task['id']}" not in st.session_state:
                        st.session_state[f"show_edit_form_{task['id']}"] = False

                    if st.button(f"Edit Details {task['id']}", key=f"edit_task_btn_{task['id']}"):
                        st.session_state[f"show_edit_form_{task['id']}"] = not st.session_state[f"show_edit_form_{task['id']}"]
                        st.experimental_rerun() # Rerun to show/hide the expander

                    if st.session_state[f"show_edit_form_{task['id']}"]:
                        with st.expander(f"Editing {task['title']}", expanded=True):
                            edit_task_form(task, all_users) # Pass all users data
                            # Add a button to explicitly close the form
                            if st.button("Close Edit Form", key=f"close_edit_btn_{task['id']}"):
                                st.session_state[f"show_edit_form_{task['id']}"] = False
                                st.experimental_rerun() # Rerun to collapse the expander

                    # Delete button with confirmation
                    if st.button(f"Delete Task {task['id']}", key=f"delete_task_btn_{task['id']}"):
                        # Simple confirmation for delete
                        if st.warning("Are you sure you want to delete this task? This action cannot be undone."):
                            if st.button(f"Confirm Delete Task {task['id']}", key=f"confirm_delete_btn_{task['id']}"):
                                if delete_task(task['id']):
                                    st.success("Task deleted.")
                                    st.experimental_rerun()
                                else:
                                    st.error("Failed to delete task.")
                                
                st.markdown("<br>") # Spacer between cards


# --- Main App Logic ---
if "logged_in" not in st.session_state:
    st.session_state["logged_in"] = False
if "access_token" not in st.session_state:
    st.session_state["access_token"] = None

st.sidebar.title("Project Tracker")

if not st.session_state["logged_in"]:
    st.sidebar.subheader("Account")
    auth_mode = st.sidebar.radio("Choose Mode", ["Login", "Register"])
    if auth_mode == "Login":
        show_login_page()
    else:
        show_registration_page()
else:
    show_main_app()