from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    pass

class Listing(models.Model):
  title = models.CharField(max_length=64)
  description = models.TextField()
  starting_bid = models.DecimalField(max_digits=10, decimal_places=2)
  image_url = models.URLField(blank=True)
  category = models.CharField(max_length=64, blank=True)
  active = models.BooleanField(default=True)
  creator = models.ForeignKey(User, on_delete=models.CASCADE, related_name="listings")
  current_price = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
  watchers = models.ManyToManyField(User, related_name="watchlist", blank=True)

  def __str__(self):
    return f"{self.title} ({self.creator.username})"

class Bid(models.Model):
  amount = models.DecimalField(max_digits=10, decimal_places=2)
  user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="bids")
  listing = models.ForeignKey(Listing, on_delete=models.CASCADE, related_name="bids")
  placed_at = models.DateTimeField(auto_now_add=True)  # Track when the bid was placed

  def __str__(self):
    return f"Bid of ${self.amount} by {self.user.username} on {self.listing.title}"

class Comment(models.Model):
  content = models.TextField()
  user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="comments")
  listing = models.ForeignKey(Listing, on_delete=models.CASCADE, related_name="comments")
  created_at = models.DateTimeField(auto_now_add=True)

  def __str__(self):
    return f"Comment by {self.user.username} on {self.listing.title}"
