"use client";
import { useState } from "react";
import { Container, Row, Col, Form, Button } from "react-bootstrap";
import { toast, ToastContainer } from "react-toastify";
import "react-toastify/dist/ReactToastify.css";
import styles from "../styles/form.module.css";

function MyForm() {
  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [nameError, setNameError] = useState("");
  const [emailError, setEmailError] = useState("");
  const [submitted, setSubmitted] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();

    let valid = true;

    if (name.trim() === "") {
      setNameError("Name is required");
      valid = false;
    } else {
      setNameError("");
    }

    if (email.trim() === "") {
      setEmailError("Email is required");
      valid = false;
    } else if (!/\S+@\S+\.\S+/.test(email)) {
      setEmailError("Invalid email address");
      valid = false;
    } else {
      setEmailError("");
    }

    if (!valid) {
      return;
    }

    const pendingToastId = toast(`Subscribing ${name} to Ticket Barter...`, {
      autoClose: false,
    });

    try {
      const response = await fetch("/api/upload", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ name, email }),
      });

      const result = await response.json();

      toast.update(pendingToastId, {
        render: "🦄 Welcome to Ticket Barter Family!",
        autoClose: 5000,
        hideProgressBar: false,
        closeOnClick: true,
        pauseOnHover: true,
        draggable: true,
        progress: undefined,
        theme: "light",
      });

      setSubmitted(true);
    } catch (error) {
      toast.error("Error submitting form, Please try again.");
      toast.dismiss(pendingToastId);
    }
  };

  return (
    <Container className={styles.container}>
      <Row>
        <Col md={7}>
          <img src={"/logo.png"} className={styles.logo} />
          <h1 className={styles.heading}>Coming Soon...</h1>
          {!submitted ? ( // Display form if not submitted
            <>
              <p className={styles.para}>
                Do you have event tickets you can’t use or don’t want? Trade
                them on Ticket Barter. Sign up to be the first to know when the
                website is live.
              </p>
              <Form onSubmit={handleSubmit}>
                <Form.Group controlId="name">
                  <Form.Control
                    className={styles.formInput}
                    type="text"
                    placeholder="Enter Your Name"
                    value={name}
                    onChange={(e) => setName(e.target.value)}
                  />
                  <Form.Text className="text-danger">{nameError}</Form.Text>
                </Form.Group>
                <Form.Group controlId="email">
                  <Form.Control
                    className={styles.formInput}
                    type="email"
                    placeholder="Enter Your Email"
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                  />
                  <Form.Text className="text-danger">{emailError}</Form.Text>
                </Form.Group>
                <Button className={styles.btn} type="submit">
                  Submit
                </Button>
              </Form>
            </>
          ) : (
            <div style={{ marginTop: "50px" }}>
              <p className={styles.para}>
                You have successfully subscribed to Ticket Barter!
              </p>
            </div>
          )}
        </Col>
        <Col md={5}></Col>
      </Row>
      <ToastContainer />
    </Container>
  );
}

export default MyForm;
