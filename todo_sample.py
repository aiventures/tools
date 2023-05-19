""" sample program demoing todo.py """

from tools.todo import Todo

todo_list = ["x  2020-12-02 2020-12-01 Python with Deskbike @Computer +Python @Deskbike +Health",
             "x  2020-12-02 2020-12-01 Python with Deskbike +Python +Health @Computer @Deskbike"
             "x 2020-12-20 Visit Stuttgart +Friend @Offsite due:2020-12-12 other_attribute:34",
             "(A) 2020-8-20 NO ATTRIBUTES due:2020-12-12",
             "2020-11-20 Yet another task + @Offsite due:2020-12-12",
             "(C) Visit Another +Friend @Offsite due:2020-12-12",
             "(C) Visit Another HASH +Friend @Offsite hash:45rerererer due:2020-12-12"
             ]

# transform from string list to dict
todo_dict = Todo.get_dict_from_todo(todo_list, show_info=False)
# transform back from dict to string
todo_list = Todo.get_todo_from_dict(todo_dict, show_info=False)
print("\n".join(todo_list))
