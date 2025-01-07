"""
converters.py
Ian Kollipara <ian.kollipara@cune.edu>
2025-01-05

Click Type Converters
"""

from click import ParamType

from coursework.loaders import Configuration, User


class AssignmentParamType(ParamType):
    """
    # AssignmentParamType.

    A custom converter to resolve assignments from strings into their assignment.
    """

    name = "assignment"

    def convert(self, value, param, ctx):
        if isinstance(value, Configuration.Assignment):
            return value

        if ctx is None or not ("config" in ctx.obj and isinstance(ctx.obj["config"], Configuration)):
            self.fail("Configuration is not defined. Cannot resolve Assignment", param, ctx)

        config: Configuration = ctx.obj["config"]

        if "_selected_course" in ctx.obj:
            course: Configuration.Course = ctx.obj["_selected_course"]
            if value not in course.assignments:
                self.fail(f"{value} is not a part of the selected course", param, ctx)

            return course.assignments[value]

        else:
            for course in config.courses.values():
                if value in course.assignments:
                    return course.assignments[value]

        self.fail(f"{value} is not a valid assignment.", param, ctx)


class CourseParamType(ParamType):
    """
    # CourseParamType.

    A custom converter to resolve courses from strings into their course.
    """

    name = "course"

    def convert(self, value, param, ctx):
        if isinstance(value, Configuration.Course):
            return value

        if ctx is None or not ("config" in ctx.obj and isinstance(ctx.obj["config"], Configuration)):
            self.fail("Configuration is not defined. Cannot resolve Course", param, ctx)

        config: Configuration = ctx.obj["config"]
        user: User = ctx.obj["user"]

        if value not in config.courses:
            self.fail(f"{value} is not a valid course.", param, ctx)

        if not user.is_instructor:
            user_courses = [name for name, course in config.courses.items() if user.name in course.students]
            if value not in user_courses:
                self.fail("You are not a member of this course.", param, ctx)

        # We set this so we can check in the Assignment Param Type.
        # That way we can validate the assignment is apart of the course.
        ctx.obj["_selected_course"] = config.courses[value]

        return config.courses[value]
