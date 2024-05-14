from django.contrib.auth import authenticate, login, logout
from django.db import IntegrityError
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render, get_object_or_404
from django.urls import reverse
from django import forms
from .models import User, Listing, Bid
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
    print(request.user)
    print(listing_id)
    listing = get_object_or_404(Listing, pk=listing_id)
    current_bid = listing.bids.order_by('-amount').first()
    is_on_watchlist = False #request.user.is_authenticated and listing.watchers.filter(user=request.user).exists()
    comments = [] #listing.comments.all().order_by('-created_at')

    # ... rest of the view logic (bidding, closing, etc.)

    return render(request, 'auctions/listing.html', {
        'listing': listing,
        'current_bid': current_bid,
        'is_on_watchlist': is_on_watchlist,
        'comments': comments,
    })