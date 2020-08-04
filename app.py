
from flask import Flask, render_template, url_for, request, redirect, session
import hashlib
import datetime

app = Flask(__name__)
app.config.from_pyfile("config.py")

from models import db
from models import Usuarios as usuario
from models import Productos, Pedidos, ItemsPedidos
def acceso(root, referrer):
    origen = referrer if referrer != None else ""
    return request.url_root in origen
    
@app.route("/", methods=["POST", "GET"])
def inicio():
    if request.method == "POST":
        password=hashlib.md5(bytes(request.form["pass"], encoding='utf-8')).hexdigest()
        user = usuario.query.filter_by(DNI=request.form["dni"]).first()
        if user:
            if password == user.Clave:
                if user.Tipo.lower() == "mozo":
                    return redirect(url_for("Mozo", dniuser=user.DNI))
                else:
                    return redirect(url_for("Chef", dniuser=user.DNI))
            else:
                return render_template("index.html", paserror="Contraseña Incorrecta")
        else:
            return render_template("index.html", dnierror="DNI Incorrecto")
    else:
        return render_template("index.html")

@app.route("/Mozo/<dniuser>")
def Mozo(dniuser):
        if acceso(request.url_root, request.referrer):
            return render_template("Mozo.html", usuario=dniuser)
        return redirect(url_for("inicio"))
@app.route("/Mozo/<dniuser>/Visualizar/<ped>", methods=["POST","GET"])
def Visualizar(dniuser, ped):
    if True: #acceso(request.url_root, request.referrer):
        if ped !="q":
            pedido=Pedidos.query.filter_by(NumPedido=ped).first()
            pedido.Cobrado=True
            db.session.commit()
            estado="Pedido {} Cobrado exitosamente".format(ped)
            pedidos = Pedidos.query.filter_by(Cobrado=False).all()
            return render_template("Visualizar.html", usuario=dniuser, pedidos=pedidos, cobro=estado)
        else:
            pedidos = Pedidos.query.filter_by(Cobrado=False).all()
            if pedidos:
                return render_template("Visualizar.html", usuario=dniuser, pedidos=pedidos)
            else:
                return render_template("Visualizar.html", usuario=dniuser, pedidos=False)
    else:
        return redirect(url_for("inicio"))

@app.route("/Chef/<dniuser>", methods=["GET", "POST"])
def Chef(dniuser):
    if True: #acceso(request.url_root, request.referrer):
        guardado=False
        if request.method=="POST":
            for i in request.form: #Cambiando a listo el estado de los items seleccionados
                item = ItemsPedidos.query.filter_by(NumItem=i).first()
                item.Estado="Listo"
                db.session.commit()
            guardado=True
        aux=[]
        for pedido in Pedidos.query.all(): #Filtrando los pedidos Con items Pendientes
            if pedido.Items.filter_by(Estado="Pendiente").all():
                aux.append(pedido)
        if guardado:
            return render_template("Chef.html", usuario=dniuser, pedidos=aux, guardado="Se ha Guardardo satisfactoriamente")
        else:
            return render_template("Chef.html", usuario=dniuser, pedidos=aux)
    return redirect(url_for("inicio"))
@app.route("/Mozo/<dniuser>/Pedido/<new>", methods=["POST"])
def NuevoPedido(dniuser, new):
    if new == "q":
        return render_template("Nuevos.html", usuario=dniuser, productos=Productos.query.all())
    else:
        items=[]
        totalpedido=0
        for i in request.form:
            if i != "Mesa" and i != "observaciones":
                producto=Productos.query.filter_by(Nombre=i).first()
                items.append(ItemsPedidos(Estado="Pendiente", 
                                    NumProducto=producto.NumProducto,
                                    Precio=producto.PrecioUnitario))
                totalpedido += float(producto.PrecioUnitario)
        pedido=Pedidos(Fecha=datetime.datetime.today(), 
                        Mesa=request.form["Mesa"], 
                        DNIMozo=dniuser,
                        Cobrado=False,
                        Observacion= request.form["observaciones"], 
                        Total = totalpedido)
        db.session.add(pedido)
        db.session.commit()
        numpedido=Pedidos.query.all()[-1].NumPedido #Ultimo pedido agregado
        for item in items:
            item.NumPedido=numpedido
            db.session.add(item)
        db.session.commit()
        return render_template("Nuevos.html", usuario=dniuser, productos=Productos.query.all(), message="Pedido añadido")
if __name__ == "__main__":
    db.create_all()
    app.run(debug=True)
    