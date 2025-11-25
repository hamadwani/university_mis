from . import db
from datetime import datetime

# -------------------------
# STUDENT MODEL
# -------------------------
class Student(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    roll_no = db.Column(db.String(10), unique=True, nullable=False)
    name = db.Column(db.String(20), nullable=False)
    email = db.Column(db.String(15))
    phone = db.Column(db.String(10))
    dob = db.Column(db.String(20))
    gender = db.Column(db.String(20))
    address = db.Column(db.String(300))  
    

    department = db.Column(db.String(200))
    programme = db.Column(db.String(200))
    year = db.Column(db.Integer)
    # bus = db.Column(db.String(30))

    profile_pic = db.Column(db.String(300), default="default.png")

    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationship → Each student can have multiple enrollments
    enrollments = db.relationship("Enrollment", backref="student", lazy=True)

    def __repr__(self):
        return f"<Student {self.roll_no} - {self.name}>"


# -------------------------
# HOSTEL MODEL ()
# -------------------------
class Hostel(db.Model):
    id = db.Column(db.Integer, primary_key=True)

    # Hostel name
    name = db.Column(db.String(120), nullable=False)

    # Warden name (you used this in forms/routes)
    warden = db.Column(db.String(120))

    # Optional hostel type (Boys/Girls/Mixed)
    type = db.Column(db.String(80))

    # Capacity + number of students currently residing
    capacity = db.Column(db.Integer, default=0)
    students_residing = db.Column(db.Integer, default=0)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"<Hostel {self.name}>"

# -------------------------
# DEPARTMENT MODEL
# -------------------------
class Department(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    code = db.Column(db.String(50))
    hod = db.Column(db.String(200))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationship → a department has many programmes
    programmes = db.relationship("Programme", backref="department", lazy=True, cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Department {self.name}>"
    



# -------------------------
# PROGRAMME MODEL
# -------------------------
class Programme(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    department_id = db.Column(db.Integer, db.ForeignKey("department.id"), nullable=False)

    # General programme info
    programme = db.Column(db.String(200), nullable=False)   # programme name
    level = db.Column(db.String(80))                        # UG/PG/Diploma etc.
    year_of_start = db.Column(db.String(20))
    admission_criteria = db.Column(db.String(200))
    duration_years = db.Column(db.Integer)
    duration_months = db.Column(db.Integer)
    exam_system = db.Column(db.String(80))                  # Semester / Annual
    approved_by = db.Column(db.String(200))                 # University/authority

    # Approved intake — category-wise
    seats_general = db.Column(db.Integer, default=0)
    seats_sc = db.Column(db.Integer, default=0)
    seats_st = db.Column(db.Integer, default=0)
    seats_obc = db.Column(db.Integer, default=0)
    seats_ews = db.Column(db.Integer, default=0)
    seats_supernumerary = db.Column(db.Integer, default=0)

    # seats_total is computed on the fly (not stored)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def seats_total(self):
        # Auto-calc total
        return ( (self.seats_general or 0) + (self.seats_sc or 0) + (self.seats_st or 0) +
                 (self.seats_obc or 0) + (self.seats_ews or 0) + (self.seats_supernumerary or 0) )

    def __repr__(self):
        return f"<Programme {self.programme} ({self.level})>"


# -------------------------
# ENROLLMENT MODEL
# -------------------------
class Enrollment(db.Model):
    id = db.Column(db.Integer, primary_key=True)

    # NEW → Link enrollment to student
    student_id = db.Column(db.Integer, db.ForeignKey("student.id"), nullable=True)

    programme = db.Column(db.String(200))
    year = db.Column(db.Integer)
    mode = db.Column(db.String(50))  

    general_male = db.Column(db.Integer, default=0)
    general_female = db.Column(db.Integer, default=0)
    ews_male = db.Column(db.Integer, default=0)
    ews_female = db.Column(db.Integer, default=0)
    sc_male = db.Column(db.Integer, default=0)
    sc_female = db.Column(db.Integer, default=0)
    st_male = db.Column(db.Integer, default=0)
    st_female = db.Column(db.Integer, default=0)
    obc_male = db.Column(db.Integer, default=0)
    obc_female = db.Column(db.Integer, default=0)
    trans_gender = db.Column(db.Integer, default=0)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)


# -------------------------
# PLACEMENT MODEL
# -------------------------
class Placement(db.Model):
    id = db.Column(db.Integer, primary_key=True)

    company = db.Column(db.String(200), nullable=False)
    role = db.Column(db.String(200))
    date = db.Column(db.String(50))
    details = db.Column(db.Text)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"<Placement {self.company}>"




# -------------------------
# STAFF MODEL
# -------------------------
from datetime import datetime
from app import db

class Staff(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)

    # NEW — Better structured fields
    staff_type = db.Column(db.String(120))  # Teaching / Non-Teaching / Contractual / Visiting etc.
    group = db.Column(db.String(50))        # Academic, Administrative, Technical, Support etc.
    sanctioned_strength = db.Column(db.Integer, default=0)

    # Category-wise gender count
    general_male = db.Column(db.Integer, default=0)
    general_female = db.Column(db.Integer, default=0)
    general_transgender = db.Column(db.Integer, default=0)

    ews_male = db.Column(db.Integer, default=0)
    ews_female = db.Column(db.Integer, default=0)
    ews_transgender = db.Column(db.Integer, default=0)

    sc_male = db.Column(db.Integer, default=0)
    sc_female = db.Column(db.Integer, default=0)
    sc_transgender = db.Column(db.Integer, default=0)

    st_male = db.Column(db.Integer, default=0)
    st_female = db.Column(db.Integer, default=0)
    st_transgender = db.Column(db.Integer, default=0)

    obc_male = db.Column(db.Integer, default=0)
    obc_female = db.Column(db.Integer, default=0)
    obc_transgender = db.Column(db.Integer, default=0)

    # NEW — Track joining date
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # ------- DERIVED DATA METHODS --------

    def total_strength(self):
        return (
            self.general_male + self.general_female + self.general_transgender +
            self.ews_male + self.ews_female + self.ews_transgender +
            self.sc_male + self.sc_female + self.sc_transgender +
            self.st_male + self.st_female + self.st_transgender +
            self.obc_male + self.obc_female + self.obc_transgender
        )

    @property
    def staff_code(self):
        """Auto generates a printable staff code"""
        return f"KU-STAFF-{self.id:03}"

    @property
    def formatted_join_date(self):
        """Return formatted joining date for UI & PDF"""
        return self.created_at.strftime("%d %B %Y") if self.created_at else "-"

    def to_dict(self):
        """Useful for JSON export or future API"""
        return {
            "id": self.id,
            "name": self.name,
            "staff_code": self.staff_code,
            "staff_type": self.staff_type,
            "group": self.group,
            "sanctioned_strength": self.sanctioned_strength,
            "total_strength": self.total_strength(),
            "joined_on": self.formatted_join_date
        }

    def __repr__(self):
        return f"<Staff {self.name} ({self.staff_code})>"


# -------------------------
# SCHOLARSHIP MODEL
# -------------------------
class Scholarship(db.Model):
    id = db.Column(db.Integer, primary_key=True)

    # Your actual fields
    title = db.Column(db.String(200), nullable=False)
    amount = db.Column(db.String(50))
    criteria = db.Column(db.String(300))

    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"<Scholarship {self.title}>"


# -------------------------
# NSS MODEL
# -------------------------
class NSSEnrollment(db.Model):
    __tablename__ = "nss_enrollment"

    id = db.Column(db.Integer, primary_key=True)

    male = db.Column(db.Integer, default=0)
    female = db.Column(db.Integer, default=0)

    @property
    def total(self):
        return (self.male or 0) + (self.female or 0)

    activity = db.Column(db.String(255), nullable=False)
    date = db.Column(db.String(50))
    remarks = db.Column(db.Text)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)




# Examination Result model
class ExamResult(db.Model):
    __tablename__ = "exam_result"

    id = db.Column(db.Integer, primary_key=True)
    programme = db.Column(db.String(150), nullable=False)

    # Category-wise stats
    general_male = db.Column(db.Integer, default=0)
    general_female = db.Column(db.Integer, default=0)
    general_transgender = db.Column(db.Integer, default=0)

    ews_male = db.Column(db.Integer, default=0)
    ews_female = db.Column(db.Integer, default=0)
    ews_transgender = db.Column(db.Integer, default=0)

    sc_male = db.Column(db.Integer, default=0)
    sc_female = db.Column(db.Integer, default=0)
    sc_transgender = db.Column(db.Integer, default=0)

    st_male = db.Column(db.Integer, default=0)
    st_female = db.Column(db.Integer, default=0)
    st_transgender = db.Column(db.Integer, default=0)

    obc_male = db.Column(db.Integer, default=0)
    obc_female = db.Column(db.Integer, default=0)
    obc_transgender = db.Column(db.Integer, default=0)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def total(self):
        return (
            self.general_male + self.general_female + self.general_transgender +
            self.ews_male + self.ews_female + self.ews_transgender +
            self.sc_male + self.sc_female + self.sc_transgender +
            self.st_male + self.st_female + self.st_transgender +
            self.obc_male + self.obc_female + self.obc_transgender
        )
