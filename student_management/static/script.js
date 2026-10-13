const $ = (id) => document.getElementById(id);
const fields = ["roll_no", "name", "email", "course", "year", "grade"];
let students = [];

const esc = (s) =>
    String(s).replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));

function toast(msg) {
    const t = $("toast");
    t.textContent = msg;
    t.classList.add("show");
    setTimeout(() => t.classList.remove("show"), 2200);
}

async function api(url, method = "GET", body) {
    const res = await fetch(url, {
        method,
        headers: { "Content-Type": "application/json" },
        body: body ? JSON.stringify(body) : undefined,
    });
    const data = await res.json();
    if (!res.ok) throw new Error(data.error || "Something went wrong.");
    return data;
}

async function load() {
    students = await api("/api/students");
    render();
}

function render() {
    const q = $("search").value.trim().toLowerCase();
    const course = $("courseFilter").value;

    // course filter options
    const courses = [...new Set(students.map((s) => s.course))].sort();
    $("courseFilter").innerHTML =
        '<option value="">All courses</option>' +
        courses.map((c) => `<option ${c === course ? "selected" : ""}>${esc(c)}</option>`).join("");

    const shown = students.filter(
        (s) =>
            (!course || s.course === course) &&
            [s.name, s.roll_no, s.email].some((v) => v.toLowerCase().includes(q))
    );

    $("rows").innerHTML = shown
        .map(
            (s) => `<tr>
        <td>${esc(s.roll_no)}</td>
        <td>${esc(s.name)}<small>${esc(s.email)}</small></td>
        <td>${esc(s.course)}</td>
        <td>${s.year}</td>
        <td><span class="pill">${s.grade}</span></td>
        <td class="btns">
          <button class="btn small edit" data-edit="${s.id}">Edit</button>
          <button class="btn small danger" data-del="${s.id}">Delete</button>
        </td>
      </tr>`
        )
        .join("");

    $("empty").hidden = shown.length > 0;
    $("empty").textContent = students.length
        ? "No students match your search."
        : "No students yet. Fill in the form to add the first one.";

    // stats
    $("statTotal").textContent = students.length;
    $("statCourses").textContent = courses.length;
    const avg = students.length ? students.reduce((a, s) => a + s.grade, 0) / students.length : 0;
    $("statAvg").textContent = avg.toFixed(1);
}

function resetForm() {
    $("studentForm").reset();
    $("sid").value = "";
    $("formTitle").textContent = "Add student";
    $("saveBtn").textContent = "Add student";
    $("cancelBtn").hidden = true;
    $("formError").textContent = "";
}

$("studentForm").addEventListener("submit", async (e) => {
    e.preventDefault();
    const body = Object.fromEntries(fields.map((f) => [f, $(f).value]));
    const id = $("sid").value;
    try {
        await api(id ? `/api/students/${id}` : "/api/students", id ? "PUT" : "POST", body);
        toast(id ? "Student updated" : "Student added");
        resetForm();
        await load();
    } catch (err) {
        $("formError").textContent = err.message;
    }
});

$("cancelBtn").addEventListener("click", resetForm);
$("search").addEventListener("input", render);
$("courseFilter").addEventListener("change", render);

$("rows").addEventListener("click", async (e) => {
    const editId = e.target.dataset.edit;
    const delId = e.target.dataset.del;
    if (editId) {
        const s = students.find((x) => x.id == editId);
        fields.forEach((f) => ($(f).value = s[f]));
        $("sid").value = s.id;
        $("formTitle").textContent = "Edit student";
        $("saveBtn").textContent = "Save changes";
        $("cancelBtn").hidden = false;
        $("name").focus();
    }
    if (delId && confirm("Delete this student?")) {
        try {
            await api(`/api/students/${delId}`, "DELETE");
            toast("Student deleted");
            await load();
        } catch (err) {
            toast(err.message);
        }
    }
});

load();