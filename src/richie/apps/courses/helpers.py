"""
Helpers that can be useful throughout Richie's courses app
"""
from .factories import CategoryFactory


def create_categories(info, parent, should_publish=True):
    """
    Create the category tree from the SUBJECTS dictionary.


    Arguments:
        info (List): definition of the category tree to create in the following format:

            {
                "title": "Subject",
                "children": [
                    {
                        "title": "Computer science",
                        "children": [
                            {"title": "Coding"},
                            {"title": "Security"},
                        ],
                    },
                    {"title": "Languages"},
                ],
            }

        page (cms.models.pagemodel.Page): Instance of a Page below which the category
            tree is created.

    Returns:
        generator[courses.models.Category]: yield only the leaf categories of the created tree.

    """
    category = CategoryFactory(
        page_title=info["title"],
        page_in_navigation=info.get("in_navigation", True),
        page_parent=parent,
        should_publish=should_publish,
    )

    if info.get("children", None):
        for child_info in info["children"]:
            yield from create_categories(
                child_info, category.extended_object, should_publish=should_publish
            )
    else:
        # we only return leaf categories (no children)
        yield category
