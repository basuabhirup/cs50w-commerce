from django.contrib.auth import authenticate, login, logout
from django.db import IntegrityError
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from django import forms
from .models import User, Listing, Bid, Comment
from django.contrib.auth.decorators import login_required


class CreateListingForm(forms.ModelForm):
    class Meta:
        model = Listing
        fields = ["title", "description", "starting_bid", "image_url", "category"]
        

def index(request):    
    active_listings = Listing.objects.filter(active=True)
    return render(request, "auctions/index.html", {"active_listings": active_listings})


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


@login_required
def create_listing(request):
  if request.method == "POST":
    form = CreateListingForm(request.POST)
    if form.is_valid():
      form.save(commit=False)  # Don't commit yet, set creator field
      form.instance.creator = request.user  # Set creator to current user
      form.save()
      return HttpResponseRedirect(reverse("index"))
  else:
    form = CreateListingForm()
  return render(request, "auctions/create_listing.html", {"form": form})


def listing(request, listing_id):
    listing = get_object_or_404(Listing, pk=listing_id)
    current_bid = listing.bids.order_by('-amount').first()
    is_on_watchlist = request.user.is_authenticated and listing.watchers.filter(username=request.user).exists()
    comments = listing.comments.all().order_by('-created_at')

    if request.method == 'POST' and request.user.is_authenticated:
        if 'add_to_watchlist' in request.POST:
            listing.watchers.add(request.user)
            listing.save()
            return redirect('watchlist')
        elif 'remove_from_watchlist' in request.POST:
            listing.watchers.remove(request.user)
            listing.save()
            return redirect('listing', listing_id=listing.id)
        
        if 'bid' in request.POST:
            new_bid = float(request.POST['bid'])
            if new_bid > listing.starting_bid and (not current_bid or new_bid > current_bid.amount):
                bid = Bid(user=request.user, listing=listing, amount=new_bid)
                bid.save()
                listing.current_price = new_bid
                listing.save()
                return redirect('listing', listing_id=listing.id)
            else:
                return render(request, 'auctions/listing.html', {
                    'listing': listing,
                    'current_bid': current_bid,
                    'is_on_watchlist': is_on_watchlist,
                    'comments': comments,
                    'error_message': 'Invalid bid or bid amount is too low.',
                })

        if 'close_auction' in request.POST and listing.creator == request.user and listing.active:
            listing.active = False
            if current_bid:
                listing.winner = current_bid.user
            else:
                listing.winner = None
            listing.save()
            return redirect('listing', listing_id=listing.id)

        if "comment" in request.POST:
            comment_text = request.POST["comment"]
            if comment_text.strip():
                print(comment_text)
                Comment.objects.create(
                    listing=listing,
                    user=request.user,
                    content=comment_text,
                )
                return redirect("listing", listing_id=listing.id)
            else:
                return render(request, 'auctions/listing.html', {
                    'listing': listing,
                    'current_bid': current_bid,
                    'is_on_watchlist': is_on_watchlist,
                    'comments': comments,
                    'error_message': 'Invalid comment.',
                })
            

    return render(request, 'auctions/listing.html', {
        'listing': listing,
        'current_bid': current_bid,
        'is_on_watchlist': is_on_watchlist,
        'comments': comments,
    })
    

@login_required
def watchlist(request):
    if request.user.is_authenticated:
        user = request.user
        watchlist_items = user.watchlist.all()
        return render(request, "auctions/watchlist.html", {
            "watchlist_items": watchlist_items,
        })
    else:
        return redirect("login")