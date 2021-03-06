import re
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.db import IntegrityError
from django.http import HttpRequest, HttpResponse, HttpResponseRedirect
from django.shortcuts import get_object_or_404, render
from django.urls import reverse

from .forms import *
from .models import *


def index(request):
    return render(request, "auctions/index.html", {
        "listings": Listing.objects.all()
    })


def login_view(request):
    if request.method == "POST":

        # Attempt to sign user in
        username = request.POST["username"]
        password = request.POST["password"]
        user = authenticate(request, username=username, password=password)

        # Check if authentication successful
        if user is not None:
            login(request, user)
            return HttpResponseRedirect(reverse("index"))
        else:
            return render(request, "auctions/login.html", {
                "message": "Invalid username and/or password."
            })
    else:
        return render(request, "auctions/login.html")


def logout_view(request):
    logout(request)
    return HttpResponseRedirect(reverse("index"))


def register(request):
    if request.method == "POST":
        username = request.POST["username"]
        email = request.POST["email"]

        # Ensure password matches confirmation
        password = request.POST["password"]
        confirmation = request.POST["confirmation"]
        if password != confirmation:
            return render(request, "auctions/register.html", {
                "message": "Passwords must match."
            })

        # Attempt to create new user
        try:
            user = User.objects.create_user(username, email, password)
            user.save()
        except IntegrityError:
            return render(request, "auctions/register.html", {
                "message": "Username already taken."
            })
        login(request, user)
        return HttpResponseRedirect(reverse("index"))
    else:
        return render(request, "auctions/register.html")


def create_listing(request):
    user = request.user

    if request.method == 'POST':
        form = ListingForm(request.POST)

        if form.is_valid():
            title = form.cleaned_data['title']
            description = form.cleaned_data['description']
            price = form.cleaned_data['price']
            photo = form.cleaned_data['photo']

            listing = Listing(user=user, name=title, photo=photo,
                              description=description, price=price)
            listing.save()

            return HttpResponseRedirect('/')
    else:
        return render(request, "auctions/create-listing.html", {
            "form": ListingForm()
        })


def listing(request, id):
    user = request.user

    if request.method == "POST":

        # If user commented
        if "comment_submit" in request.POST:
            form = CommentForm(request.POST)
            
            if form.is_valid():
                comment = form.cleaned_data['comment']
                listing = Listing.objects.get(pk=id)

                comment_obj, created = Comment.objects.get_or_create(user=user, comment=comment)
                comment_obj.listings.add(listing)

                print(comment_obj)
                
                # print(Comment.objects.get(pk=2).listings.all())  
                # comment_obj, created = Comment.objects.get_or_create(user=user)


                return HttpResponseRedirect(reverse('listing', args=[id]))
            else:
                # print(form.errors.as_data())
                return render(request, "auctions/listing.html", {
                    "comment": form
                })

        # If user pressed "Close Auction".
        if "close" in request.POST:
            listing = Listing.objects.get(id=id)
            listing.active = False
            listing.save()

            # The listing is not saved in winner's watchlist so
            # we must add it.
            winner = Bid.objects.filter(listing=id).latest('bid').user
    
            watchlist_obj, created = Watchlist.objects.get_or_create(user=winner)
            watchlist_obj.listings.add(listing)

            return HttpResponseRedirect('/')
        else:
            form = BidForm(request.POST)

            if form.is_valid():
                bid = form.cleaned_data["bid"]

                listing = Listing.objects.get(id=id)

                print(listing.id)

                # Check if bid is higher than price.
                if bid > listing.price:
                    listing.price = bid
                    listing.save()

                    Bid.objects.create(user=user, listing=listing, bid=bid)
                else:
                    messages.add_message(
                        request, messages.ERROR, 'Place a higher bid.')

                return HttpResponseRedirect(reverse('listing', args=[id]))
    else:
        listing = Listing.objects.get(pk=id)
        print(Comment.objects.get(pk=id).comment)
        comments = Comment.objects.filter(listings__id=id)
        print(comments)

        # Check if item is in watchlist
        if Watchlist.objects.filter(user=user.id).filter(listings__id=id).exists():
            button = "Remove"
        else:
            button = "Watchlist"

        # Check if the user has the highest bid
        bid = Bid.objects.filter(listing=listing)

        # Check if user is the one who created the listing
        if user.id == listing.user.id:
            close = "Close Auction"

            if not bid:
                pass
            else:
                bid = bid.latest('bid')

                # Check if logged user has the highest bid
                if bid.user == user:
                    return render(request, "auctions/listing.html", {
                        "pk": listing.id,
                        "name": listing.name,
                        "photo": listing.photo,
                        "description": listing.description,
                        "price": listing.price,
                        "form": BidForm(),
                        "button": button,
                        "close": close,
                        "active": listing.active,
                        "message": "You have the highest bid.",
                        "comment": CommentForm(),
                        'comments': comments
                    })
                else:
                    return render(request, "auctions/listing.html", {
                        "pk": listing.id,
                        "name": listing.name,
                        "photo": listing.photo,
                        "description": listing.description,
                        "price": listing.price,
                        "form": BidForm(),
                        "button": button,
                        "active": listing.active,
                        "close": close,
                        "comment": CommentForm(),
                        'comments': comments
                    })

            return render(request, "auctions/listing.html", {
                "pk": listing.id,
                "name": listing.name,
                "photo": listing.photo,
                "description": listing.description,
                "price": listing.price,
                "form": BidForm(),
                "button": button,
                "active": listing.active,
                "close": close,
                "comment": CommentForm(),
                'comments': comments
            })
        else:
            username = listing.user.username

            if not bid:
                pass
            else:
                bid = bid.latest('bid')
                # Check if the user has the highest bid
                if bid.user == user:
                    return render(request, "auctions/listing.html", {
                        "pk": listing.id,
                        "username": username,
                        "name": listing.name,
                        "photo": listing.photo,
                        "description": listing.description,
                        "price": listing.price,
                        "form": BidForm(),
                        "button": button,
                        "active": listing.active,
                        "message": "You have the highest bid.",
                        "comment": CommentForm(),
                        'comments': comments
                    })
                else:
                    return render(request, "auctions/listing.html", {
                        "pk": listing.id,
                        "username": username,
                        "name": listing.name,
                        "photo": listing.photo,
                        "description": listing.description,
                        "price": listing.price,
                        "form": BidForm(),
                        "active": listing.active,
                        "button": button,
                        "comment": CommentForm(),
                        'comments': comments
                    })

            return render(request, "auctions/listing.html", {
                "pk": listing.id,
                "username": username,
                "name": listing.name,
                "photo": listing.photo,
                "description": listing.description,
                "price": listing.price,
                "form": BidForm(),
                "active": listing.active,
                "button": button,
                "comment": CommentForm(),
                'comments': comments
            })


def watchlist(request):
    user = request.user
    watchlist_obj, created = Watchlist.objects.get_or_create(user=user)

    if request.method == "POST":
        pk = int(request.POST.get('pk'))
        listing = Listing.objects.get(pk=pk)

        # Remove or add item
        if Watchlist.objects.filter(user=user).filter(listings__id=pk).exists():
            watchlist_obj.listings.remove(listing)
        else:
            watchlist_obj.listings.add(listing)

        return HttpResponseRedirect('/')
    else:
        watchlist = Watchlist.objects.filter(user=user.id).get()

        return render(request, "auctions/watchlist.html", {
            "watchlist": watchlist
        })