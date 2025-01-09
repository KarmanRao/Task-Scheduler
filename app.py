from flask import Flask, render_template, request, redirect, url_for
import heapq
from datetime import datetime, timedelta

app = Flask(__name__)

class Task:
    def __init__(self, name, priority, deadline, duration, dependencies=None):
        self.name = name
        self.priority = priority  
        self.deadline = datetime.strptime(deadline, "%Y-%m-%d %H:%M")

        self.duration = timedelta(hours=duration)
        self.dependencies = dependencies or []
        self.status = "Pending"

    def __lt__(self, other):
        return (self.priority, self.deadline) < (other.priority, other.deadline)

class TaskScheduler:
    def __init__(self):
        self.tasks = []  
        self.task_graph = {}  

    def add_task(self, name, priority, deadline, duration, dependencies=None):
        task = Task(name, priority, deadline, duration, dependencies)
        heapq.heappush(self.tasks, task)
        self.task_graph[name] = task

    def view_tasks(self):
        return sorted(self.tasks, key=lambda x: (x.priority, x.deadline))

    def delete_task(self, name):
        self.tasks = [task for task in self.tasks if task.name != name]
        heapq.heapify(self.tasks)
        if name in self.task_graph:
            del self.task_graph[name]

    def schedule_tasks(self):
        sorted_tasks = self.topological_sort()
        if sorted_tasks is None:
            return None  

        schedule = []
        current_time = datetime.now()

        for task in sorted_tasks:
            if task.deadline >= current_time:
                schedule.append((current_time, task))
                current_time += task.duration

        return schedule

    def topological_sort(self):
        in_degree = {task: 0 for task in self.task_graph}

        for task in self.task_graph.values():
            for dep in task.dependencies:
                if dep in in_degree:
                    in_degree[dep] += 1

        queue = [task for task, degree in in_degree.items() if degree == 0]
        sorted_tasks = []

        while queue:
            current = queue.pop(0)
            sorted_tasks.append(self.task_graph[current])

            for dep in self.task_graph[current].dependencies:
                in_degree[dep] -= 1
                if in_degree[dep] == 0:
                    queue.append(dep)

        if len(sorted_tasks) != len(self.task_graph):
            return None  

        return sorted_tasks

scheduler = TaskScheduler()

@app.route('/')
def index():
    tasks = scheduler.view_tasks()
    return render_template('index.html', tasks=tasks)

@app.route('/add', methods=['GET', 'POST'])
def add_task():
    if request.method == 'POST':
        name = request.form['name']
        priority = int(request.form['priority'])
        deadline = request.form['deadline']
        duration = int(request.form['duration'])
        dependencies = request.form.get('dependencies', '').split(',')
        dependencies = [dep.strip() for dep in dependencies if dep.strip()]
        scheduler.add_task(name, priority, deadline, duration, dependencies)
        return redirect(url_for('index'))
    return render_template('add_task.html')

@app.route('/delete/<string:name>')
def delete_task(name):
    scheduler.delete_task(name)
    return redirect(url_for('index'))

@app.route('/schedule')
def schedule_tasks():
    schedule = scheduler.schedule_tasks()
    if schedule is None:
        return "Task dependencies contain a cycle. Cannot schedule tasks."
    return render_template('schedule.html', schedule=schedule)

if __name__ == '__main__':
    app.run(debug=True)
