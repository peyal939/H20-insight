from flask import Blueprint, request, render_template, session, redirect, url_for
from models.db import get_cursor

# Create support blueprint
support_bp = Blueprint('support', __name__)

@support_bp.route("/support") 
def support():
    cur, db = get_cursor()
    
    # If the user is a Admin get all the tickets that have not been resolved yet 
    if session["user_type"] == "A":
        cur.execute("SELECT * FROM tickets WHERE status = 0")
        tickets = cur.fetchall()
    
    # If the user is a researcher or a viewer get all tickets that he has submitted
    else:
        query = "SELECT * FROM tickets WHERE user_id = %s ORDER BY date DESC"
        data = (int(session.get("user_id")), )
        cur.execute(query, data)
        tickets = cur.fetchall()

    cur.close()
    db.close()
    
    return render_template("support.html", tickets=tickets)


# Shows resolved tickets (FOR ADMIN ONLY)
@support_bp.route("/resolved_tickets")
def resolved_tickets():
    if session.get("user_type") != "A":
        session["error_massage"] = "This page is only for admins."
        return redirect("/apology")
    
    cur, db = get_cursor()
    cur.execute("SELECT * FROM tickets WHERE status = 1")
    tickets = cur.fetchall()
    cur.close()
    db.close()
    
    return render_template("support.html", tickets=tickets, resolve_flag=True)


@support_bp.route("/support_form", methods=["GET", "POST"]) # Support form and support form input handaling
def submit_support():
    if request.method == "GET":
        return render_template("support_form.html")

    if request.method == "POST":
        subject = request.form.get("subject")
        description = request.form.get("description")
        user_id = session.get("user_id")

        if not subject or not description:
            session["error_massage"] = "Subject and discription is mandatory"
            return redirect("/apology")
        
        if len(subject) > 255 or len(description) > 6000:
            session["error_massage"] = "Subject can not be more then 255 characters and description can not be more then 6000 characters"
            return redirect("/apology")
            
        cur, db = get_cursor()
        
        query = "INSERT INTO tickets (user_id, subject, description) VALUES (%s, %s, %s)"
        data = (int(user_id), subject, description)
        cur.execute(query, data)

        db.commit()
        cur.close()
        db.close()
        
        # Geting the support id that just have been submited
        cur, db = get_cursor()

        query = "SELECT ticket_id FROM tickets WHERE user_id = %s ORDER BY date DESC LIMIT 1"
        data = (int(session.get("user_id")), )
        cur.execute(query, data)
        ticket_id = int(cur.fetchall()[0][0])
        cur.close()
        db.close()

        return redirect(url_for("support.support_view", ticket_id=ticket_id))
    

@support_bp.route("/support_view") # View of support ticket and masseging
def support_view(): 
    ticket_id = request.args.get("ticket_id")
    
    cur, db = get_cursor()

    query = "SELECT * FROM tickets WHERE ticket_id = %s"
    data = (ticket_id, )
    cur.execute(query, data)

    ticket_tuple = cur.fetchall()[0]
    cur.close()
    db.close()

    if ticket_tuple[1] != session.get("user_id") and session["user_type"] != "A":
        session["error_massage"] = "A ticket can be viewed by only the person who made it or a Admin"
        return redirect("/apology")

    if ticket_tuple[5] == 0:
        status = "Open"
        resolved = False
    else:
        status = "Resolved"
        resolved = True

    ticket_data = {
        "Status" : status,
        "Subject" : ticket_tuple[2],
        "Date" : ticket_tuple[3],
        "Description" : ticket_tuple[4],
        "ticket_id" : ticket_id,
        "user_id" : ticket_tuple[1],
        "resolved" : resolved
    }

    # Get all the messages of this ticket
    cur, db = get_cursor()

    query = "SELECT text, user_type, user_name, date FROM messages JOIN users ON messages.user_id = users.user_id WHERE ticket_id = %s ORDER BY date ASC"
    data = (int(ticket_id), )
    cur.execute(query, data)

    if cur.rowcount == 0:
        messeges = None
    
    else:
        messeges = cur.fetchall()
       
    cur.close()
    db.close()

    return render_template("support_view.html", ticket_data=ticket_data, messeges=messeges)


@support_bp.route("/send_massage", methods=["POST"])
def send_massage():
    if request.method == "POST":
        user_id = session.get("user_id")
        ticket_id = int(request.form.get("ticket_id"))
        message = request.form.get("massage")
        

        # Checks if the ticket is closed or not
        cur, db = get_cursor()
        cur.execute("SELECT status FROM tickets WHERE ticket_id = %s", (int(ticket_id), ))
        check = cur.fetchall()[0][0]
        if int(check) == 1:
            session["error_massage"] = "Massage cant be sent to a closed ticket"
            return redirect("/apology")

        if len(message) > 2000:
            session["error_massage"] = "Sorry, We only support massage that are less then 2000 characters"
            return redirect("/apology")

        cur, db = get_cursor()
        
        query = "INSERT INTO messages (user_id, ticket_id, text) VALUES (%s, %s, %s)"
        data = (user_id, ticket_id, message)
        cur.execute(query, data)

        db.commit()
        cur.close()
        db.close()

        return redirect(url_for("support.support_view", ticket_id=ticket_id))


# Closing a ticket
@support_bp.route("/close_ticket", methods=["POST"])
def close_ticket():
    if session["user_type"] != "A":
        session["error_massage"] = "Only a admin can close the ticket"
        return redirect("/apology")
    
    ticket_id = request.form.get("ticket_id")
    
    cur, db = get_cursor()

    query = "UPDATE tickets SET status = 1 WHERE ticket_id = %s"
    data = (int(ticket_id), )
    cur.execute(query, data)

    db.commit()
    cur.close()
    db.close()

    return redirect(url_for("support.resolved_tickets")) 