"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { FormEvent, useEffect, useState } from "react";
import {
  Address,
  AddressInput,
  ApiError,
  ProfileInput,
  UserProfile,
  authApi,
  clearSession,
  hasSession,
  userApi,
} from "@/lib/api";

const emptyAddress: AddressInput = {
  label: "home",
  recipient_name: "",
  phone: null,
  address_line1: "",
  address_line2: null,
  city: "",
  state: "",
  postal_code: "",
  country: "",
  is_default: false,
};

function addressToInput(address: Address): AddressInput {
  return {
    label: address.label,
    recipient_name: address.recipient_name,
    phone: address.phone,
    address_line1: address.address_line1,
    address_line2: address.address_line2,
    city: address.city,
    state: address.state,
    postal_code: address.postal_code,
    country: address.country,
    is_default: address.is_default,
  };
}

export default function AccountPage() {
  const router = useRouter();
  const [profile, setProfile] = useState<UserProfile | null>(null);
  const [addresses, setAddresses] = useState<Address[]>([]);
  const [loading, setLoading] = useState(true);
  const [savingProfile, setSavingProfile] = useState(false);
  const [savingAddress, setSavingAddress] = useState(false);
  const [formOpen, setFormOpen] = useState(false);
  const [editingAddress, setEditingAddress] = useState<Address | null>(null);
  const [addressDraft, setAddressDraft] = useState<AddressInput>(emptyAddress);
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");

  useEffect(() => {
    if (!hasSession()) {
      router.replace("/login");
      return;
    }

    async function loadAccount() {
      try {
        const [nextProfile, nextAddresses] = await Promise.all([
          userApi.getProfile(),
          userApi.getAddresses(),
        ]);
        setProfile(nextProfile);
        setAddresses(nextAddresses);
      } catch (cause) {
        if (cause instanceof ApiError && cause.status === 401) {
          clearSession();
          router.replace("/login");
          return;
        }
        setError(
          cause instanceof ApiError
            ? cause.message
            : "We couldn't load your account. Please try again.",
        );
      } finally {
        setLoading(false);
      }
    }

    void loadAccount();
  }, [router]);

  async function handleProfileSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!profile) return;

    const form = new FormData(event.currentTarget);
    const update: ProfileInput = {
      full_name: String(form.get("full_name") ?? ""),
      phone: String(form.get("phone") ?? "") || null,
      date_of_birth: String(form.get("date_of_birth") ?? "") || null,
      avatar_url: profile.avatar_url,
    };
    setSavingProfile(true);
    setError("");
    setMessage("");
    try {
      setProfile(await userApi.updateProfile(update));
      setMessage("Your details are all up to date.");
    } catch (cause) {
      setError(
        cause instanceof ApiError
          ? cause.message
          : "We couldn't save your details. Please try again.",
      );
    } finally {
      setSavingProfile(false);
    }
  }

  function openNewAddress() {
    setEditingAddress(null);
    setAddressDraft(emptyAddress);
    setFormOpen(true);
    setError("");
    setMessage("");
  }

  function openEditAddress(address: Address) {
    setEditingAddress(address);
    setAddressDraft(addressToInput(address));
    setFormOpen(true);
    setError("");
    setMessage("");
  }

  async function handleAddressSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const form = new FormData(event.currentTarget);
    const draft: AddressInput = {
      label: String(form.get("label") ?? "home"),
      recipient_name: String(form.get("recipient_name") ?? ""),
      phone: String(form.get("phone") ?? "") || null,
      address_line1: String(form.get("address_line1") ?? ""),
      address_line2: String(form.get("address_line2") ?? "") || null,
      city: String(form.get("city") ?? ""),
      state: String(form.get("state") ?? ""),
      postal_code: String(form.get("postal_code") ?? ""),
      country: String(form.get("country") ?? ""),
      is_default: form.get("is_default") === "on",
    };
    setSavingAddress(true);
    setError("");
    setMessage("");
    try {
      const saved = editingAddress
        ? await userApi.updateAddress(editingAddress.id, draft)
        : await userApi.createAddress(draft);
      setAddresses((current) => {
        const updated = editingAddress
          ? current.map((address) =>
              address.id === saved.id ? saved : address,
            )
          : [...current, saved];
        return saved.is_default
          ? updated.map((address) => ({
              ...address,
              is_default: address.id === saved.id,
            }))
          : updated;
      });
      setFormOpen(false);
      setEditingAddress(null);
      setMessage(editingAddress ? "Address updated." : "Address added.");
    } catch (cause) {
      setError(
        cause instanceof ApiError
          ? cause.message
          : "We couldn't save this address. Please try again.",
      );
    } finally {
      setSavingAddress(false);
    }
  }

  async function handleDeleteAddress(address: Address) {
    if (!window.confirm(`Remove the ${address.label} address?`)) return;
    setError("");
    setMessage("");
    try {
      await userApi.deleteAddress(address.id);
      setAddresses((current) =>
        current.filter((item) => item.id !== address.id),
      );
      setMessage("Address removed.");
    } catch (cause) {
      setError(
        cause instanceof ApiError
          ? cause.message
          : "We couldn't remove this address. Please try again.",
      );
    }
  }

  async function handleLogout() {
    setError("");
    try {
      await authApi.logout();
      router.replace("/");
    } catch (cause) {
      setError(
        cause instanceof ApiError
          ? cause.message
          : "We couldn't sign you out. Please try again.",
      );
    }
  }

  if (loading || !profile) {
    return <div className="loading-state">Getting your little corner ready…</div>;
  }

  return (
    <main className="account-shell">
      <div className="announcement">
        Thoughtful things for everyday living <span aria-hidden="true">✳</span>
      </div>
      <header className="site-header">
        <Link className="wordmark" href="/" aria-label="Nook home">
          nook<span>.</span>
        </Link>
        <nav className="header-nav" aria-label="Account navigation">
          <Link href="/">Home</Link>
          <a href="#addresses">Your addresses</a>
        </nav>
        <button className="button button-outline button-small" onClick={handleLogout}>
          Sign out <span aria-hidden="true">↗</span>
        </button>
      </header>

      <div className="account-main">
        <div className="account-top">
          <div>
            <p className="eyebrow"><span className="eyebrow-dot" /> YOUR LITTLE CORNER</p>
            <h1 className="account-title">Hello, {profile.full_name.split(" ")[0]}.</h1>
            <p className="account-intro">
              Make yourself at home. Your details are right here.
            </p>
          </div>
        </div>

        {error && <p className="form-error" role="alert">{error}</p>}
        {message && <p className="form-success" role="status">{message}</p>}

        <div className="account-layout">
          <nav className="account-nav" aria-label="Account sections">
            <a className="active" href="#profile">Personal details</a>
            <a href="#addresses">Saved addresses</a>
          </nav>

          <div className="account-content">
            <section className="panel" id="profile">
              <div className="panel-heading">
                <div>
                  <h2>Personal details</h2>
                  <p>A few details to make this feel more like yours.</p>
                </div>
              </div>
              <form onSubmit={handleProfileSubmit}>
                <div className="profile-grid">
                  <div className="form-field form-field-wide">
                    <label htmlFor="profile-email">Email address</label>
                    <input id="profile-email" value={profile.email} readOnly />
                  </div>
                  <div className="form-field form-field-wide">
                    <label htmlFor="profile-name">Full name</label>
                    <input
                      id="profile-name"
                      name="full_name"
                      minLength={2}
                      maxLength={255}
                      defaultValue={profile.full_name}
                      required
                    />
                  </div>
                  <div className="form-field">
                    <label htmlFor="profile-phone">Phone</label>
                    <input
                      id="profile-phone"
                      name="phone"
                      type="tel"
                      maxLength={20}
                      defaultValue={profile.phone ?? ""}
                      placeholder="Add a phone number"
                    />
                  </div>
                  <div className="form-field">
                    <label htmlFor="profile-birthday">Date of birth</label>
                    <input
                      id="profile-birthday"
                      name="date_of_birth"
                      type="date"
                      defaultValue={profile.date_of_birth ?? ""}
                    />
                  </div>
                </div>
                <button className="button button-dark auth-submit" disabled={savingProfile}>
                  {savingProfile ? "Saving…" : "Save details"}
                  <span aria-hidden="true">↗</span>
                </button>
              </form>
            </section>

            <section className="panel" id="addresses">
              <div className="panel-heading">
                <div>
                  <h2>Saved addresses</h2>
                  <p>Keep your favourite places close at hand.</p>
                </div>
                {!formOpen && (
                  <button className="button button-outline" onClick={openNewAddress}>
                    + Add address
                  </button>
                )}
              </div>

              {addresses.length === 0 ? (
                <div className="empty-state">
                  No saved addresses just yet. Add one and it&apos;ll be waiting
                  here for you.
                </div>
              ) : (
                <div className="address-list">
                  {addresses.map((address) => (
                    <article className="address-card" key={address.id}>
                      <div className="address-card-top">
                        <span className="address-label">{address.label}</span>
                        {address.is_default && (
                          <span className="default-label">Default</span>
                        )}
                      </div>
                      <h3>{address.recipient_name}</h3>
                      <p>
                        {address.address_line1}
                        {address.address_line2 && <><br />{address.address_line2}</>}
                        <br />
                        {address.city}, {address.state} {address.postal_code}
                        <br />
                        {address.country}
                        {address.phone && <><br />{address.phone}</>}
                      </p>
                      <div className="address-actions">
                        <button
                          className="small-action"
                          onClick={() => openEditAddress(address)}
                        >
                          Edit
                        </button>
                        <button
                          className="small-action danger"
                          onClick={() => void handleDeleteAddress(address)}
                        >
                          Remove
                        </button>
                      </div>
                    </article>
                  ))}
                </div>
              )}

              {formOpen && (
                <form
                  key={editingAddress?.id ?? "new"}
                  className="address-form"
                  onSubmit={handleAddressSubmit}
                >
                  <div className="panel-heading">
                    <div>
                      <h2>{editingAddress ? "Edit address" : "Add an address"}</h2>
                      <p>We&apos;ll keep it safe and ready for next time.</p>
                    </div>
                  </div>
                  <div className="profile-grid">
                    <div className="form-field">
                      <label htmlFor="address-label">Label</label>
                      <select
                        id="address-label"
                        name="label"
                        defaultValue={addressDraft.label}
                      >
                        <option value="home">Home</option>
                        <option value="work">Work</option>
                        <option value="other">Other</option>
                      </select>
                    </div>
                    <div className="form-field">
                      <label htmlFor="recipient-name">Recipient name</label>
                      <input
                        id="recipient-name"
                        name="recipient_name"
                        minLength={2}
                        maxLength={255}
                        defaultValue={addressDraft.recipient_name}
                        required
                      />
                    </div>
                    <div className="form-field form-field-wide">
                      <label htmlFor="address-line1">Address line 1</label>
                      <input
                        id="address-line1"
                        name="address_line1"
                        maxLength={255}
                        defaultValue={addressDraft.address_line1}
                        required
                      />
                    </div>
                    <div className="form-field form-field-wide">
                      <label htmlFor="address-line2">Address line 2 <span>(optional)</span></label>
                      <input
                        id="address-line2"
                        name="address_line2"
                        maxLength={255}
                        defaultValue={addressDraft.address_line2 ?? ""}
                      />
                    </div>
                    <div className="form-field">
                      <label htmlFor="address-city">City</label>
                      <input
                        id="address-city"
                        name="city"
                        maxLength={100}
                        defaultValue={addressDraft.city}
                        required
                      />
                    </div>
                    <div className="form-field">
                      <label htmlFor="address-state">State / region</label>
                      <input
                        id="address-state"
                        name="state"
                        maxLength={100}
                        defaultValue={addressDraft.state}
                        required
                      />
                    </div>
                    <div className="form-field">
                      <label htmlFor="postal-code">Postal code</label>
                      <input
                        id="postal-code"
                        name="postal_code"
                        maxLength={20}
                        defaultValue={addressDraft.postal_code}
                        required
                      />
                    </div>
                    <div className="form-field">
                      <label htmlFor="address-country">Country</label>
                      <input
                        id="address-country"
                        name="country"
                        maxLength={100}
                        defaultValue={addressDraft.country}
                        required
                      />
                    </div>
                    <div className="form-field">
                      <label htmlFor="address-phone">Phone <span>(optional)</span></label>
                      <input
                        id="address-phone"
                        name="phone"
                        type="tel"
                        maxLength={20}
                        defaultValue={addressDraft.phone ?? ""}
                      />
                    </div>
                    <label className="checkbox-row">
                      <input
                        name="is_default"
                        type="checkbox"
                        defaultChecked={addressDraft.is_default}
                      />
                      Make this my default address
                    </label>
                  </div>
                  <div className="form-actions">
                    <button className="button button-dark" disabled={savingAddress}>
                      {savingAddress ? "Saving…" : "Save address"}
                    </button>
                    <button
                      className="button button-plain"
                      type="button"
                      onClick={() => setFormOpen(false)}
                    >
                      Cancel
                    </button>
                  </div>
                </form>
              )}
            </section>
          </div>
        </div>
      </div>
    </main>
  );
}
