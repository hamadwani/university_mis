from flask import Blueprint, render_template, request, redirect, url_for, flash, make_response
from . import db
from .models import (
    Student, Hostel, Department, Programme,
    Enrollment, Placement, Staff, Scholarship,
    NSSEnrollment, ExamResult
)

from io import BytesIO
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors

main = Blueprint("main", __name__)

# =====================================================
# DASHBOARD
# =====================================================
@main.route("/")
def dashboard():
    enrollments = Enrollment.query.order_by(Enrollment.created_at.desc()).limit(5).all()
    students = Student.query.order_by(Student.created_at.desc()).limit(5).all()

    labels = []
    values = []
    yearly_data = {}

    for e in Enrollment.query.all():
        if e.year not in yearly_data:
            yearly_data[e.year] = 0
        yearly_data[e.year] += (
            (e.general_male or 0) + (e.general_female or 0) +
            (e.ews_male or 0) + (e.ews_female or 0) +
            (e.sc_male or 0) + (e.sc_female or 0) +
            (e.st_male or 0) + (e.st_female or 0) +
            (e.obc_male or 0) + (e.obc_female or 0) +
            (e.trans_gender or 0)
        )

    for y in sorted(yearly_data):
        labels.append(str(y))
        values.append(yearly_data[y])

    return render_template(
        "dashboard.html",
        enrollments=enrollments,
        students=students,
        enrollment_graph_labels=labels,
        enrollment_graph_data=values,
    )


# =====================================================
# STUDENT MODULE
# =====================================================
@main.route("/students", methods=["GET"])
def students():
    search_query = request.args.get("search")

    if search_query:
        students = Student.query.filter(
            (Student.roll_no.ilike(f"%{search_query}%")) |
            (Student.name.ilike(f"%{search_query}%"))
        ).all()
    else:
        students = Student.query.all()

    return render_template("students/students.html", students=students, search_query=search_query)



@main.route("/students/add", methods=["GET", "POST"])
def add_student():
    if request.method == "POST":
        roll_no = request.form.get("roll_no")
        # if len(roll_no) > 11:
        #     return "Roll number cannot exceed 10 digits!"
        name = request.form.get("name")

        if not roll_no or not name:
            flash("Roll Number and Name are required!", "danger")
            return redirect(url_for("main.add_student"))

        new_student = Student(
            roll_no=roll_no,
            name=name,
            email=request.form.get("email"),
            phone=request.form.get("phone"),
            dob=request.form.get("dob"),
            gender=request.form.get("gender"),
            address=request.form.get("address"),
            department=request.form.get("department"),
            programme=request.form.get("programme"),
            year=request.form.get("year"),
            # bus=request.form.get("bus")
        )
        db.session.add(new_student)
        db.session.commit()
        flash("Student added successfully!", "success")
        return redirect(url_for("main.students"))

    return render_template("students/add_student.html")


@main.route("/student/<int:id>")
def student_profile(id):
    student = Student.query.get_or_404(id)
    return render_template("students/student_profile.html", student=student)


@main.route("/students/edit/<int:id>", methods=["GET", "POST"])
def edit_student(id):
    student = Student.query.get_or_404(id)

    if request.method == "POST":
        student.roll_no = request.form.get("roll_no")
        student.name = request.form.get("name")
        student.email = request.form.get("email")
        student.phone = request.form.get("phone")
        student.dob = request.form.get("dob")
        student.gender = request.form.get("gender")
        student.address = request.form.get("address")
        student.department = request.form.get("department")
        student.programme = request.form.get("programme")
        student.year = request.form.get("year")

        db.session.commit()
        flash("Student updated!", "info")
        return redirect(url_for("main.students"))

    return render_template("students/edit_student.html", student=student)


@main.route("/students/delete/<int:id>")
def delete_student(id):
    st = Student.query.get_or_404(id)
    db.session.delete(st)
    db.session.commit()
    flash("Student deleted!", "danger")
    return redirect(url_for("main.students"))


# ----------------------------------------------------
# STUDENT PDF EXPORT
# ----------------------------------------------------
@main.route("/student/pdf/<int:id>")
def student_pdf(id):
    s = Student.query.get_or_404(id)

    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4)

    styles = getSampleStyleSheet()
    story = []

    story.append(Paragraph("<b>Student Profile</b>", styles["Title"]))
    story.append(Spacer(1, 12))

    fields = [
        ["Roll No", s.roll_no],
        ["Name", s.name],
        ["Email", s.email],
        ["Phone", s.phone],
        ["DOB", s.dob],
        ["Gender", s.gender],
        ["Address", s.address],
        ["Department", s.department],
        ["Programme", s.programme],
        ["Year", s.year]
    ]

    table = Table(fields, colWidths=[150, 300])
    table.setStyle(TableStyle([
        ("GRID", (0, 0), (-1, -1), 1, colors.grey),
        ("BACKGROUND", (0, 0), (-1, 0), colors.lightgrey)
    ]))
    story.append(table)

    doc.build(story)
    pdf = buffer.getvalue()
    buffer.close()

    response = make_response(pdf)
    response.headers["Content-Type"] = "application/pdf"
    response.headers["Content-Disposition"] = f"attachment; filename=student_{s.id}.pdf"
    return response


# =====================================================
# ENROLLMENT
# =====================================================
@main.route("/enrollment", methods=["GET", "POST"])
def enrollment():
    students = Student.query.all()

    if request.method == "POST":
        student_id = request.form.get("student_id")

        if student_id != "none":
            std = Student.query.get(student_id)
            programme = std.programme
            year = std.year
            mode = "Regular"
        else:
            programme = request.form["programme"]
            year = request.form["year"]
            mode = request.form["mode"]

        record = Enrollment(
            student_id=student_id if student_id != "none" else None,
            programme=programme,
            year=year,
            mode=mode,
            general_male=request.form.get("general_male") or 0,
            general_female=request.form.get("general_female") or 0,
            ews_male=request.form.get("ews_male") or 0,
            ews_female=request.form.get("ews_female") or 0,
            sc_male=request.form.get("sc_male") or 0,
            sc_female=request.form.get("sc_female") or 0,
            st_male=request.form.get("st_male") or 0,
            st_female=request.form.get("st_female") or 0,
            obc_male=request.form.get("obc_male") or 0,
            obc_female=request.form.get("obc_female") or 0,
            trans_gender=request.form.get("trans_gender") or 0
        )

        db.session.add(record)
        db.session.commit()
        flash("Enrollment saved!", "success")
        return redirect(url_for("main.enrollment"))

    enrollments = Enrollment.query.order_by(Enrollment.created_at.desc()).all()
    return render_template("enrollment/enrollment.html", students=students, enrollments=enrollments)


@main.route("/enrollment/edit/<int:id>", methods=["GET", "POST"])
def edit_enrollment(id):
    e = Enrollment.query.get_or_404(id)

    if request.method == "POST":
        e.programme = request.form["programme"]
        e.year = request.form["year"]
        e.mode = request.form["mode"]

        e.general_male = request.form.get("general_male") or 0
        e.general_female = request.form.get("general_female") or 0
        e.ews_male = request.form.get("ews_male") or 0
        e.ews_female = request.form.get("ews_female") or 0
        e.sc_male = request.form.get("sc_male") or 0
        e.sc_female = request.form.get("sc_female") or 0
        e.st_male = request.form.get("st_male") or 0
        e.st_female = request.form.get("st_female") or 0
        e.obc_male = request.form.get("obc_male") or 0
        e.obc_female = request.form.get("obc_female") or 0
        e.trans_gender = request.form.get("trans_gender") or 0

        db.session.commit()
        flash("Enrollment updated!", "info")
        return redirect(url_for("main.enrollment"))

    return render_template("enrollment/edit_enrollment.html", e=e)


@main.route("/enrollment/<int:id>")
def enrollment_profile(id):
    e = Enrollment.query.get_or_404(id)
    return render_template("enrollment/enrollment_profile.html", enrollment=e)


@main.route("/enrollment/delete/<int:id>", methods=["POST"])
def delete_enrollment(id):
    e = Enrollment.query.get_or_404(id)
    db.session.delete(e)
    db.session.commit()
    flash("Enrollment deleted!", "danger")
    return redirect(url_for("main.enrollment"))


# ------------------------------------------------
# ENROLLMENT PDF EXPORT
# ------------------------------------------------
@main.route("/enrollment/pdf/<int:id>")
def enrollment_pdf(id):
    e = Enrollment.query.get_or_404(id)

    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4)
    styles = getSampleStyleSheet()
    story = []

    story.append(Paragraph("<b>Enrollment Report</b>", styles["Title"]))
    story.append(Spacer(1, 12))

    story.append(Paragraph(f"<b>Programme:</b> {e.programme}", styles["Normal"]))
    story.append(Paragraph(f"<b>Year:</b> {e.year}", styles["Normal"]))
    story.append(Paragraph(f"<b>Mode:</b> {e.mode}", styles["Normal"]))
    story.append(Spacer(1, 12))

    if e.student:
        story.append(Paragraph("<b>Linked Student</b>", styles["Heading3"]))
        story.append(Paragraph(f"Name: {e.student.name}", styles["Normal"]))
        story.append(Paragraph(f"Roll No: {e.student.roll_no}", styles["Normal"]))
        story.append(Spacer(1, 12))

    table_data = [
        ["Category", "Count"],
        ["General Male", e.general_male],
        ["General Female", e.general_female],
        ["EWS Male", e.ews_male],
        ["EWS Female", e.ews_female],
        ["SC Male", e.sc_male],
        ["SC Female", e.sc_female],
        ["ST Male", e.st_male],
        ["ST Female", e.st_female],
        ["OBC Male", e.obc_male],
        ["OBC Female", e.obc_female],
        ["Transgender", e.trans_gender]
    ]

    table = Table(table_data, colWidths=[200, 100])
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.lightgrey),
        ("GRID", (0, 0), (-1, -1), 1, colors.grey)
    ]))
    story.append(table)

    doc.build(story)
    pdf = buffer.getvalue()
    buffer.close()

    response = make_response(pdf)
    response.headers["Content-Type"] = "application/pdf"
    response.headers["Content-Disposition"] = f"attachment; filename=enrollment_{e.id}.pdf"
    return response


# =====================================================
# STAFF MODULE (SIMPLE VERSION – matches your templates)
# =====================================================
ROLES = ["Admin", "Teacher", "Librarian", "Accountant", "Staff"]

@main.route("/staff")
def staff_list():
    staff_list = Staff.query.order_by(Staff.name.asc()).all()

    total_sanctioned = sum((s.sanctioned_strength or 0) for s in staff_list)
    total_staff_count = sum((s.total_strength() or 0) for s in staff_list)

    return render_template(
        "staff/staff_list.html",
        staff_list=staff_list,
        total_sanctioned=total_sanctioned,
        total_staff_count=total_staff_count
    )



STAFF_GROUPS = ["A", "B", "C", "D"]
STAFF_TYPES = ["Permanent", "Contractual", "Teaching", "Non-Teaching"]
@main.route("/staff/add", methods=["GET", "POST"])
def add_staff():
    if request.method == "POST":
        staff = Staff(
    name=request.form.get("name"),
    staff_type=request.form.get("staff_type"),
    group=request.form.get("group"),
    sanctioned_strength=request.form.get("sanctioned_strength"),
    general_male=request.form.get("general_male") or 0,
    general_female=request.form.get("general_female") or 0,
    general_transgender=request.form.get("general_transgender") or 0,
    ews_male=request.form.get("ews_male") or 0,
    ews_female=request.form.get("ews_female") or 0,
    ews_transgender=request.form.get("ews_transgender") or 0,
    sc_male=request.form.get("sc_male") or 0,
    sc_female=request.form.get("sc_female") or 0,
    sc_transgender=request.form.get("sc_transgender") or 0,
    st_male=request.form.get("st_male") or 0,
    st_female=request.form.get("st_female") or 0,
    st_transgender=request.form.get("st_transgender") or 0,
    obc_male=request.form.get("obc_male") or 0,
    obc_female=request.form.get("obc_female") or 0,
    obc_transgender=request.form.get("obc_transgender") or 0,
)

        db.session.add(staff)
        db.session.commit()
        flash("Staff added successfully!", "success")
        return redirect(url_for("main.staff_list"))

    return render_template("staff/add_staff.html", STAFF_TYPES=STAFF_TYPES, STAFF_GROUPS=STAFF_GROUPS)


@main.route("/staff/edit/<int:staff_id>", methods=["GET", "POST"])
def edit_staff(staff_id):
    staff = Staff.query.get_or_404(staff_id)

    if request.method == "POST":
        staff.name = request.form.get("name")
        staff.type = request.form.get("type")
        staff.position = request.form.get("position")
        staff.category = request.form.get("category")

        db.session.commit()
        flash("Staff updated!", "info")
        return redirect(url_for("main.staff_list"))

    return render_template("staff/edit_staff.html", staff=staff, roles=ROLES)


@main.route("/staff/profile/<int:staff_id>")
def staff_profile(staff_id):
    staff = Staff.query.get_or_404(staff_id)
    return render_template("staff/staff_profile.html", staff=staff)


@main.route("/staff/delete/<int:staff_id>", methods=["GET", "POST"])
def delete_staff(staff_id):
    staff = Staff.query.get_or_404(staff_id)

    if request.method == "POST":
        db.session.delete(staff)
        db.session.commit()
        flash("Staff deleted!", "danger")
        return redirect(url_for("main.staff_list"))

    return render_template("staff/staff_delete_confirm.html", staff=staff)


# ------------------------------------------------
# STAFF ID CARD PDF EXPORT
# ------------------------------------------------
@main.route("/staff/pdf/<int:id>")
def staff_pdf(id):
    s = Staff.query.get_or_404(id)

    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4)
    styles = getSampleStyleSheet()
    story = []

    story.append(Paragraph("<b>Staff ID Card</b>", styles["Title"]))
    story.append(Spacer(1, 12))

    fields = [
        ["Name", s.name],
        ["Type", s.type],
        ["Position", s.position],
        ["Category", s.category]
    ]

    table = Table(fields, colWidths=[150, 300])
    table.setStyle(TableStyle([
        ("GRID", (0, 0), (-1, -1), 1, colors.grey),
        ("BACKGROUND", (0, 0), (-1, 0), colors.lightgrey)
    ]))
    story.append(table)

    doc.build(story)
    pdf = buffer.getvalue()
    buffer.close()

    response = make_response(pdf)
    response.headers["Content-Type"] = "application/pdf"
    response.headers["Content-Disposition"] = f"attachment; filename=staff_{s.id}.pdf"
    return response


# =====================================================
# DEPARTMENTS
# =====================================================
@main.route("/departments")
def departments():
    depts = Department.query.order_by(Department.name.asc()).all()
    return render_template("departments/departments.html", departments=depts)


@main.route("/departments/add", methods=["GET", "POST"])
def add_department():
    if request.method == "POST":
        name = request.form.get("name")
        code = request.form.get("code")
        hod = request.form.get("hod")

        if not name:
            flash("Department name is required", "danger")
            return redirect(url_for("main.add_department"))

        dept = Department(name=name, code=code, hod=hod)
        db.session.add(dept)
        db.session.commit()
        flash("Department added!", "success")
        return redirect(url_for("main.departments"))
    return render_template("departments/add_department.html")


@main.route("/departments/edit/<int:dept_id>", methods=["GET", "POST"])
def edit_department(dept_id):
    dept = Department.query.get_or_404(dept_id)
    if request.method == "POST":
        dept.name = request.form.get("name")
        dept.code = request.form.get("code")
        dept.hod = request.form.get("hod")
        db.session.commit()
        flash("Department updated!", "info")
        return redirect(url_for("main.departments"))
    return render_template("departments/edit_department.html", department=dept)


@main.route("/departments/delete/<int:dept_id>", methods=["GET", "POST"])
def delete_department(dept_id):
    dept = Department.query.get_or_404(dept_id)
    if request.method == "POST":
        db.session.delete(dept)
        db.session.commit()
        flash("Department deleted!", "danger")
        return redirect(url_for("main.departments"))
    return render_template("departments/department_delete_confirm.html", department=dept)


@main.route("/departments/<int:dept_id>")
def department_profile(dept_id):
    dept = Department.query.get_or_404(dept_id)
    programmes = Programme.query.filter_by(department_id=dept.id).order_by(Programme.programme.asc()).all()
    return render_template("departments/department_profile.html", department=dept, programmes=programmes)


@main.route("/departments/pdf/<int:dept_id>")
def department_pdf(dept_id):
    dept = Department.query.get_or_404(dept_id)
    programmes = Programme.query.filter_by(department_id=dept.id).all()

    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4)
    styles = getSampleStyleSheet()
    story = []

    story.append(Paragraph(f"<b>Department Report — {dept.name}</b>", styles["Title"]))
    if dept.code:
        story.append(Paragraph(f"Code: {dept.code}", styles["Normal"]))
    if dept.hod:
        story.append(Paragraph(f"HOD: {dept.hod}", styles["Normal"]))
    story.append(Spacer(1, 12))

    data = [
        ["Programme", "Level", "Year start", "Duration (Y/M)", "Exam", "Approved By",
         "Gen", "SC", "ST", "OBC", "EWS", "Super", "Total"]
    ]

    for p in programmes:
        data.append([
            p.programme,
            p.level or "-",
            p.year_of_start or "-",
            f"{p.duration_years or '-'} / {p.duration_months or '-'}",
            p.exam_system or "-",
            p.approved_by or "-",
            p.seats_general or 0,
            p.seats_sc or 0,
            p.seats_st or 0,
            p.seats_obc or 0,
            p.seats_ews or 0,
            p.seats_supernumerary or 0,
            p.seats_total()
        ])

    table = Table(data, colWidths=[120, 40, 45, 70, 50, 80, 30, 30, 30, 30, 30, 45, 40])
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.lightgrey),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
        ("FONT", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("ALIGN", (6, 1), (-1, -1), "CENTER")
    ]))

    story.append(table)
    doc.build(story)

    pdf = buffer.getvalue()
    buffer.close()

    response = make_response(pdf)
    response.headers["Content-Type"] = "application/pdf"
    response.headers["Content-Disposition"] = f"attachment; filename=department_{dept.id}.pdf"
    return response


# =====================================================
# PROGRAMMES (Inside Department)
# =====================================================
@main.route("/departments/<int:dept_id>/programmes")
def programmes(dept_id):
    dept = Department.query.get_or_404(dept_id)
    programmes = Programme.query.filter_by(department_id=dept_id).all()
    return render_template("departments/programmes.html", department=dept, programmes=programmes)


@main.route("/departments/<int:dept_id>/programmes/add", methods=["GET", "POST"])
def add_programme(dept_id):
    dept = Department.query.get_or_404(dept_id)

    if request.method == "POST":
        p = Programme(
            department_id=dept_id,
            programme=request.form.get("programme"),
            level=request.form.get("level"),
            year_of_start=request.form.get("year_of_start"),
            admission_criteria=request.form.get("admission_criteria"),
            duration_years=request.form.get("duration_years"),
            duration_months=request.form.get("duration_months"),
            exam_system=request.form.get("exam_system"),
            approved_by=request.form.get("approved_by"),
            seats_general=request.form.get("seats_general") or 0,
            seats_sc=request.form.get("seats_sc") or 0,
            seats_st=request.form.get("seats_st") or 0,
            seats_obc=request.form.get("seats_obc") or 0,
            seats_ews=request.form.get("seats_ews") or 0,
            seats_supernumerary=request.form.get("seats_supernumerary") or 0,
        )

        db.session.add(p)
        db.session.commit()
        flash("Programme added successfully!", "success")
        return redirect(url_for("main.programmes", dept_id=dept_id))

    return render_template("departments/add_programme.html", department=dept)


@main.route("/programmes/edit/<int:prog_id>", methods=["GET", "POST"])
def edit_programme(prog_id):
    p = Programme.query.get_or_404(prog_id)
    dept = Department.query.get_or_404(p.department_id)

    if request.method == "POST":
        p.programme = request.form.get("programme")
        p.level = request.form.get("level")
        p.year_of_start = request.form.get("year_of_start")
        p.admission_criteria = request.form.get("admission_criteria")
        p.duration_years = request.form.get("duration_years")
        p.duration_months = request.form.get("duration_months")
        p.exam_system = request.form.get("exam_system")
        p.approved_by = request.form.get("approved_by")

        p.seats_general = request.form.get("seats_general") or 0
        p.seats_sc = request.form.get("seats_sc") or 0
        p.seats_st = request.form.get("seats_st") or 0
        p.seats_obc = request.form.get("seats_obc") or 0
        p.seats_ews = request.form.get("seats_ews") or 0
        p.seats_supernumerary = request.form.get("seats_supernumerary") or 0

        db.session.commit()
        flash("Programme updated!", "info")
        return redirect(url_for("main.programmes", dept_id=p.department_id))

    return render_template("departments/edit_programme.html", programme=p, department=dept)


@main.route("/programmes/delete/<int:prog_id>")
def delete_programme(prog_id):
    p = Programme.query.get_or_404(prog_id)
    dept_id = p.department_id

    db.session.delete(p)
    db.session.commit()
    flash("Programme deleted!", "danger")
    return redirect(url_for("main.programmes", dept_id=dept_id))


# ---------------------------
# HOSTELS MODULE
# ---------------------------
@main.route("/hostels")
def hostels():
    host_list = Hostel.query.order_by(Hostel.id.desc()).all()
    return render_template("hostels/hostels.html", hostels=host_list)


@main.route("/hostels/add", methods=["GET", "POST"])
def add_hostel():
    if request.method == "POST":
        name = request.form.get("name")
        if not name:
            flash("Hostel name is required", "danger")
            return redirect(url_for("main.add_hostel"))

        hostel = Hostel(
            name=name,
            type=request.form.get("type"),
            capacity=int(request.form.get("capacity") or 0),
            students_residing=int(request.form.get("students_residing") or 0),
            # warden only if your model has this column
            warden=request.form.get("warden") if hasattr(Hostel, "warden") else None
        )
        db.session.add(hostel)
        db.session.commit()
        flash("Hostel added!", "success")
        return redirect(url_for("main.hostels"))

    return render_template("hostels/add_hostel.html")


@main.route("/hostels/edit/<int:hostel_id>", methods=["GET", "POST"])
def edit_hostel(hostel_id):
    h = Hostel.query.get_or_404(hostel_id)

    if request.method == "POST":
        h.name = request.form.get("name")
        h.type = request.form.get("type")
        h.capacity = int(request.form.get("capacity") or 0)
        h.students_residing = int(request.form.get("students_residing") or 0)
        if hasattr(Hostel, "warden"):
            h.warden = request.form.get("warden")

        db.session.commit()
        flash("Hostel updated!", "info")
        return redirect(url_for("main.hostels"))

    return render_template("hostels/edit_hostel.html", hostel=h)


@main.route("/hostels/delete/<int:hostel_id>", methods=["POST"])
def delete_hostel(hostel_id):
    h = Hostel.query.get_or_404(hostel_id)
    db.session.delete(h)
    db.session.commit()
    flash("Hostel deleted!", "danger")
    return redirect(url_for("main.hostels"))


@main.route("/hostels/<int:hostel_id>")
def hostel_profile(hostel_id):
    h = Hostel.query.get_or_404(hostel_id)
    return render_template("hostels/hostel_profile.html", hostel=h)


@main.route("/hostels/pdf/<int:hostel_id>")
def hostel_pdf(hostel_id):
    h = Hostel.query.get_or_404(hostel_id)

    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4)
    styles = getSampleStyleSheet()
    story = []

    story.append(Paragraph(f"<b>Hostel Report — {h.name}</b>", styles["Title"]))
    story.append(Spacer(1, 8))

    story.append(Paragraph(f"<b>Name:</b> {h.name}", styles["Normal"]))
    story.append(Paragraph(f"<b>Type:</b> {getattr(h, 'type', '-') or '-'}", styles["Normal"]))
    story.append(Paragraph(f"<b>Capacity:</b> {h.capacity}", styles["Normal"]))
    story.append(Paragraph(f"<b>Students Residing:</b> {h.students_residing}", styles["Normal"]))
    if hasattr(h, "warden"):
        story.append(Paragraph(f"<b>Warden:</b> {h.warden or '-'}", styles["Normal"]))
    story.append(Spacer(1, 12))

    data = [["Field", "Value"],
            ["Name", h.name],
            ["Type", getattr(h, "type", "-") or "-"],
            ["Capacity", str(h.capacity)],
            ["Students Residing", str(h.students_residing)]]

    if hasattr(h, "warden"):
        data.append(["Warden", h.warden or "-"])

    data.append(["Created At", h.created_at.strftime("%d %b %Y")])

    table = Table(data, colWidths=[200, 260])
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.lightgrey),
        ("GRID", (0, 0), (-1, -1), 1, colors.grey),
        ("ALIGN", (0, 0), (-1, -1), "LEFT")
    ]))
    story.append(table)
    doc.build(story)

    pdf = buffer.getvalue()
    buffer.close()
    response = make_response(pdf)
    response.headers['Content-Type'] = 'application/pdf'
    response.headers['Content-Disposition'] = f'attachment; filename=hostel_{h.id}.pdf'
    return response


# =====================================================
# PLACEMENT MODULE
# =====================================================
@main.route("/placement")
def placement():
    placements = Placement.query.order_by(Placement.id.desc()).all()
    return render_template("placement/placement.html", placements=placements)


@main.route("/placement/add", methods=["GET", "POST"])
def add_placement():
    if request.method == "POST":
        p = Placement(
            company=request.form["company"],
            role=request.form.get("role"),
            date=request.form.get("date"),
            details=request.form.get("details")
        )
        db.session.add(p)
        db.session.commit()
        flash("Placement added!", "success")
        return redirect(url_for("main.placement"))

    return render_template("placement/add_placement.html")


@main.route("/placement/edit/<int:placement_id>", methods=["GET", "POST"])
def edit_placement(placement_id):
    p = Placement.query.get_or_404(placement_id)

    if request.method == "POST":
        p.company = request.form["company"]
        p.role = request.form.get("role")
        p.date = request.form.get("date")
        p.details = request.form.get("details")

        db.session.commit()
        flash("Placement updated!", "info")
        return redirect(url_for("main.placement"))

    return render_template("placement/edit_placement.html", placement=p)


@main.route("/placement/delete/<int:placement_id>")
def delete_placement(placement_id):
    p = Placement.query.get_or_404(placement_id)
    db.session.delete(p)
    db.session.commit()
    flash("Placement deleted!", "danger")
    return redirect(url_for("main.placement"))


@main.route("/placement/<int:id>")
def placement_profile(id):
    p = Placement.query.get_or_404(id)
    return render_template("placement/placement_profile.html", p=p)


@main.route("/placement/pdf/<int:id>")
def placement_pdf(id):
    p = Placement.query.get_or_404(id)

    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4)
    styles = getSampleStyleSheet()

    story = []
    story.append(Paragraph("<b>Placement Report</b>", styles["Title"]))
    story.append(Spacer(1, 12))

    story.append(Paragraph(f"<b>Company:</b> {p.company}", styles["Normal"]))
    story.append(Paragraph(f"<b>Role:</b> {p.role}", styles["Normal"]))
    story.append(Paragraph(f"<b>Date:</b> {p.date}", styles["Normal"]))
    story.append(Spacer(1, 12))
    story.append(Paragraph("<b>Details:</b>", styles["Heading2"]))
    story.append(Paragraph(p.details or "No details provided.", styles["Normal"]))

    doc.build(story)

    pdf = buffer.getvalue()
    buffer.close()

    response = make_response(pdf)
    response.headers["Content-Type"] = "application/pdf"
    response.headers["Content-Disposition"] = f"attachment; filename=placement_{p.id}.pdf"
    return response


# =====================================================
# SCHOLARSHIP MODULE
# =====================================================
@main.route("/scholarship")
def scholarship():
    scholarships = Scholarship.query.order_by(Scholarship.id.desc()).all()
    return render_template("scholarship/scholarship.html", scholarships=scholarships)


@main.route("/scholarship/add", methods=["GET", "POST"])
def add_scholarship():
    if request.method == "POST":
        s = Scholarship(
            title=request.form.get("title"),
            amount=request.form.get("amount"),
            criteria=request.form.get("criteria")
        )
        db.session.add(s)
        db.session.commit()
        flash("Scholarship added!", "success")
        return redirect(url_for("main.scholarship"))

    return render_template("scholarship/add_scholarship.html")


@main.route("/scholarship/edit/<int:scholarship_id>", methods=["GET", "POST"])
def edit_scholarship(scholarship_id):
    s = Scholarship.query.get_or_404(scholarship_id)

    if request.method == "POST":
        s.title = request.form.get("title")
        s.amount = request.form.get("amount")
        s.criteria = request.form.get("criteria")

        db.session.commit()
        flash("Scholarship updated!", "info")
        return redirect(url_for("main.scholarship"))

    return render_template("scholarship/edit_scholarship.html", scholarship=s)


@main.route("/scholarship/delete/<int:scholarship_id>", methods=["POST"])
def delete_scholarship(scholarship_id):
    s = Scholarship.query.get_or_404(scholarship_id)
    db.session.delete(s)
    db.session.commit()
    flash("Scholarship deleted!", "danger")
    return redirect(url_for("main.scholarship"))


# =====================================================
# NSS MODULE (activity + male/female counts)
# =====================================================
@main.route("/nss")
def nss_list():
    nss = NSSEnrollment.query.order_by(NSSEnrollment.id.desc()).all()
    return render_template("nss/nss.html", nss_list=nss)


@main.route("/nss/add", methods=["GET", "POST"])
def add_nss():
    if request.method == "POST":
        entry = NSSEnrollment(
            activity=request.form.get("activity"),
            date=request.form.get("date"),
            male=int(request.form.get("male") or 0),
            female=int(request.form.get("female") or 0),
            remarks=request.form.get("remarks")
        )
        db.session.add(entry)
        db.session.commit()
        flash("NSS entry added!", "success")
        return redirect(url_for("main.nss_list"))

    return render_template("nss/add_nss.html")


@main.route("/nss/edit/<int:nss_id>", methods=["GET", "POST"])
def edit_nss(nss_id):
    entry = NSSEnrollment.query.get_or_404(nss_id)

    if request.method == "POST":
        entry.activity = request.form.get("activity")
        entry.date = request.form.get("date")
        entry.male = int(request.form.get("male") or 0)
        entry.female = int(request.form.get("female") or 0)
        entry.remarks = request.form.get("remarks")

        db.session.commit()
        flash("NSS updated!", "info")
        return redirect(url_for("main.nss_list"))

    return render_template("nss/edit_nss.html", entry=entry)


@main.route("/nss/delete/<int:nss_id>", methods=["POST"])
def delete_nss(nss_id):
    entry = NSSEnrollment.query.get_or_404(nss_id)
    db.session.delete(entry)
    db.session.commit()
    flash("NSS entry deleted!", "danger")
    return redirect(url_for("main.nss_list"))


# ==========================================================
# EXAM RESULT MODULE (Format A – simple table, no totals row)
# ==========================================================
@main.route("/exam")
def exam_results():
    results = ExamResult.query.order_by(ExamResult.id.desc()).all()
    return render_template("exam/exam_results.html", results=results)


@main.route("/exam/add", methods=["GET", "POST"])
def add_exam_result():
    if request.method == "POST":
        result = ExamResult(
            programme=request.form.get("programme"),
            general_male=request.form.get("general_male") or 0,
            general_female=request.form.get("general_female") or 0,
            general_transgender=request.form.get("general_transgender") or 0,
            ews_male=request.form.get("ews_male") or 0,
            ews_female=request.form.get("ews_female") or 0,
            ews_transgender=request.form.get("ews_transgender") or 0,
            sc_male=request.form.get("sc_male") or 0,
            sc_female=request.form.get("sc_female") or 0,
            sc_transgender=request.form.get("sc_transgender") or 0,
            st_male=request.form.get("st_male") or 0,
            st_female=request.form.get("st_female") or 0,
            st_transgender=request.form.get("st_transgender") or 0,
            obc_male=request.form.get("obc_male") or 0,
            obc_female=request.form.get("obc_female") or 0,
            obc_transgender=request.form.get("obc_transgender") or 0,
        )

        db.session.add(result)
        db.session.commit()
        flash("Exam Result Added Successfully!", "success")
        return redirect(url_for("main.exam_results"))

    return render_template("exam/add_exam_result.html")


@main.route("/exam/edit/<int:exam_id>", methods=["GET", "POST"])
def edit_exam_result(exam_id):
    result = ExamResult.query.get_or_404(exam_id)

    if request.method == "POST":
        result.programme = request.form.get("programme")
        result.general_male = request.form.get("general_male") or 0
        result.general_female = request.form.get("general_female") or 0
        result.general_transgender = request.form.get("general_transgender") or 0

        result.ews_male = request.form.get("ews_male") or 0
        result.ews_female = request.form.get("ews_female") or 0
        result.ews_transgender = request.form.get("ews_transgender") or 0

        result.sc_male = request.form.get("sc_male") or 0
        result.sc_female = request.form.get("sc_female") or 0
        result.sc_transgender = request.form.get("sc_transgender") or 0

        result.st_male = request.form.get("st_male") or 0
        result.st_female = request.form.get("st_female") or 0
        result.st_transgender = request.form.get("st_transgender") or 0

        result.obc_male = request.form.get("obc_male") or 0
        result.obc_female = request.form.get("obc_female") or 0
        result.obc_transgender = request.form.get("obc_transgender") or 0

        db.session.commit()
        flash("Exam record updated successfully!", "success")
        return redirect(url_for("main.exam_results"))

    return render_template("exam/edit_exam_result.html", result=result)


@main.route("/exam/delete/<int:exam_id>", methods=["POST"])
def delete_exam_result(exam_id):
    result = ExamResult.query.get_or_404(exam_id)
    db.session.delete(result)
    db.session.commit()
    flash("Exam Result Deleted!", "danger")
    return redirect(url_for("main.exam_results"))


# ---- OPTIONAL: Export all exam results to PDF, for your button 'export_exam_pdf'
@main.route("/exam/export/pdf")
def export_exam_pdf():
    results = ExamResult.query.order_by(ExamResult.programme.asc()).all()

    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4)
    styles = getSampleStyleSheet()
    story = []

    story.append(Paragraph("<b>Exam Results Summary</b>", styles["Title"]))
    story.append(Spacer(1, 12))

    data = [["Programme", "Gen M", "Gen F", "Gen T",
             "EWS M", "EWS F", "EWS T",
             "SC M", "SC F", "SC T",
             "ST M", "ST F", "ST T",
             "OBC M", "OBC F", "OBC T"]]

    for r in results:
        data.append([
            r.programme,
            r.general_male, r.general_female, r.general_transgender,
            r.ews_male, r.ews_female, r.ews_transgender,
            r.sc_male, r.sc_female, r.sc_transgender,
            r.st_male, r.st_female, r.st_transgender,
            r.obc_male, r.obc_female, r.obc_transgender
        ])

    table = Table(data, repeatRows=1)
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.lightgrey),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
        ("FONTSIZE", (0, 0), (-1, -1), 8),
    ]))

    story.append(table)
    doc.build(story)

    pdf = buffer.getvalue()
    buffer.close()

    response = make_response(pdf)
    response.headers["Content-Type"] = "application/pdf"
    response.headers["Content-Disposition"] = "attachment; filename=exam_results.pdf"
    return response
