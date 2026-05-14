/**
 * Page transitions, scroll reveal, navbar, loader, toasts, quick view, wishlist
 */
(function () {
  "use strict";

  const html = document.documentElement;

  function setThemeFromBody() {
    const t = document.body.dataset.theme || "light";
    html.setAttribute("data-theme", t);
  }

  function hideLoader() {
    const el = document.getElementById("loader");
    if (el) {
      el.classList.add("hide");
      setTimeout(function () {
        el.remove();
      }, 500);
    }
  }

  function initLoader() {
    window.addEventListener("load", function () {
      setTimeout(hideLoader, 400);
    });
    setTimeout(hideLoader, 2500);
  }

  function initNavbar() {
    const nav = document.querySelector(".navbar-premium");
    if (!nav) return;
    const onScroll = function () {
      if (window.scrollY > 12) nav.classList.add("scrolled");
      else nav.classList.remove("scrolled");
    };
    window.addEventListener("scroll", onScroll, { passive: true });
    onScroll();
  }

  function initBackTop() {
    const btn = document.getElementById("backTop");
    if (!btn) return;
    window.addEventListener(
      "scroll",
      function () {
        if (window.scrollY > 400) btn.classList.add("show");
        else btn.classList.remove("show");
      },
      { passive: true }
    );
    btn.addEventListener("click", function () {
      window.scrollTo({ top: 0, behavior: "smooth" });
    });
  }

  function initReveal() {
    const els = document.querySelectorAll(".section-fade");
    if (!els.length) return;
    const io = new IntersectionObserver(
      function (entries) {
        entries.forEach(function (e) {
          if (e.isIntersecting) {
            e.target.classList.add("visible");
            io.unobserve(e.target);
          }
        });
      },
      { threshold: 0.12, rootMargin: "0px 0px -40px 0px" }
    );
    els.forEach(function (el) {
      io.observe(el);
    });
  }

  function showToast(message, variant) {
    const host = document.getElementById("toastHost");
    if (!host) return;
    const bg =
      variant === "success"
        ? "bg-success"
        : variant === "danger"
          ? "bg-danger"
          : variant === "warning"
            ? "bg-warning text-dark"
            : variant === "info"
              ? "bg-info text-dark"
              : "bg-dark";
    const el = document.createElement("div");
    el.className =
      "toast align-items-center text-white border-0 show mb-2 " + bg;
    el.setAttribute("role", "alert");
    el.innerHTML =
      '<div class="d-flex"><div class="toast-body">' +
      message +
      '</div><button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast"></button></div>';
    host.appendChild(el);
    setTimeout(function () {
      el.classList.remove("show");
      el.addEventListener("transitionend", function () {
        el.remove();
      });
    }, 4200);
  }

  function flashToasts() {
    try {
      var data = document.getElementById("flash-data");
      if (!data || !data.textContent || !data.textContent.trim()) return;
      var items = JSON.parse(data.textContent);
      items.forEach(function (x) {
        showToast(x[0], x[1]);
      });
    } catch (e) {
      /* ignore */
    }
  }

  function bindCartToastForms() {
    document.querySelectorAll("form[data-toast-cart]").forEach(function (form) {
      form.addEventListener("submit", function () {
        var msg = form.getAttribute("data-toast-cart") || "Added to cart";
        sessionStorage.setItem("pendingToast", msg);
      });
    });
    var pending = sessionStorage.getItem("pendingToast");
    if (pending) {
      sessionStorage.removeItem("pendingToast");
      showToast(pending, "success");
    }
  }

  function initQuickView() {
    document.querySelectorAll("[data-quick-view]").forEach(function (btn) {
      btn.addEventListener("click", function () {
        var id = btn.getAttribute("data-quick-view");
        fetch("/api/product/" + id + "/quick")
          .then(function (r) {
            return r.json();
          })
          .then(function (p) {
            document.getElementById("qv-title").textContent = p.name;
            document.getElementById("qv-price").textContent =
              "₹" + Number(p.price).toLocaleString("en-IN");
            var img = document.getElementById("qv-img");
            img.src = "/static/images/" + (p.image || "placeholder.svg");
            document.getElementById("qv-desc").textContent =
              (p.description || "").slice(0, 220) +
              ((p.description || "").length > 220 ? "…" : "");
            var link = document.getElementById("qv-link");
            link.href = "/product/" + p.id;
            var form = document.getElementById("qv-cart-form");
            form.querySelector('input[name="product_id"]').value = p.id;
            var modal = new bootstrap.Modal(
              document.getElementById("quickViewModal")
            );
            modal.show();
          })
          .catch(function () {
            showToast("Could not load product.", "danger");
          });
      });
    });
  }

  function initWishlistButtons() {
    document.querySelectorAll("form[data-wishlist]").forEach(function (form) {
      form.addEventListener("submit", function (e) {
        e.preventDefault();
        var fd = new FormData(form);
        fetch(form.action, { method: "POST", body: fd })
          .then(function (r) {
            return r.json();
          })
          .then(function (data) {
            var btn = form.querySelector(".wishlist-btn");
            if (data.in_wishlist) {
              btn.classList.add("active");
              showToast("Saved to wishlist", "success");
            } else {
              btn.classList.remove("active");
              showToast("Removed from wishlist", "info");
            }
          })
          .catch(function () {
            window.location.href = "/login";
          });
      });
    });
  }

  function initHeroCarouselFade() {
    var el = document.getElementById("heroCarousel");
    if (!el || typeof bootstrap === "undefined") return;
    el.addEventListener("slide.bs.carousel", function () {
      el.querySelectorAll(".carousel-caption").forEach(function (c) {
        c.style.opacity = "0";
        c.style.transform = "translateY(16px)";
      });
    });
    el.addEventListener("slid.bs.carousel", function () {
      var active = el.querySelector(".carousel-item.active .carousel-caption");
      if (active) {
        active.style.transition = "opacity 0.5s ease, transform 0.5s ease";
        active.style.opacity = "1";
        active.style.transform = "translateY(0)";
      }
    });
  }

  document.addEventListener("DOMContentLoaded", function () {
    setThemeFromBody();
    initLoader();
    initNavbar();
    initBackTop();
    initReveal();
    flashToasts();
    bindCartToastForms();
    initQuickView();
    initWishlistButtons();
    initHeroCarouselFade();
  });
})();
