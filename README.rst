=========
 Tacitum
=========

This is just an experiment involving two-factor authentication and —at some
point— managing a LDAP directory for authentication with multiple, per-service
passwords for each user.


Quickstart
==========

At any rate, please use a virtualenv:

.. code-block:: sh

    virtualenv venv -p $(which python3)
    source venv/bin/activate
    pip install -r requirements.txt

Users have to be created manually, fire up the ``python`` interpreter and do:

.. code-block:: python

    import store, models
    s = store.TacitumStore("data")
    s.put("/user", models.User("jdoe", name="John Doe")
    s.commit("Added user jdoe")

This will create the plain text file ``data/user/jdoe.hipack`` (actually, it
is in `HiPack <http://hipack.org>`_ format). You can check the generated
password and TOTP token from the file, or with the Python interpreter:

.. code-block:: python

    u = s.get("/user/jdoe")
    print(u.password, u.totp_key)

To run the web application, use the ``muffin`` command:

.. code-block:: sh

    muffin app run
