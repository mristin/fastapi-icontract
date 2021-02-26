************
Introduction
************

FastAPI-icontract is a `FastAPI`_ extension for design-by-contract which leverages
`icontract`_ to allow you to specify and enforce code contracts in your
`FastAPI endpoints`_.

.. _FastAPI: https://fastapi.tiangolo.com/
.. _icontract: https://github.com/Parquery/icontract
.. _FastAPI endpoints: https://fastapi.tiangolo.com/tutorial/first-steps/

Depending on how you set it up, FastAPI-icontract will:

* automatically **enforce** the contracts during testing or in production,
* automatically add the contracts to your **OpenAPI specification**, and
* render the **Swagger UI** with a specialized contracts plugin for nicer visualization.

Benefits of Adding Contracts to Your API
========================================

Enforcing code contracts in your FastAPI development opens up new venues for approaches
to more `systematic design`_ at the API level:

.. _systematic design: https://cacm.acm.org/blogs/blog-cacm/227928-why-not-program-right/fulltext

* Contracts are an important **part of the specification**.

  Unlike human language, contracts written in code are unambiguous.
* Contracts are **automatically verifiable**.

  Your clients can rest assured that you actually run them.
  FastAPI-icontract will specify precisely which contracts are run in production and
  which were only verified during testing.
* Contracts provide **deeper testing**.

  If you have a mesh of microservices that you need to test in conjunction,
  turn on all the contracts and test against your *client's* data instead of your own
  limited unit test data.
* Contracts specified in code allow for automatic **client-side** verification.

  Thus you can signal formally to the client up-front what you expect
  (using pre-conditions), while the client can verify what to expect back from you
  (using post-conditions).
* Contracts are **not just for input validation**.

  Though you can use contracts for input validation as well, FastAPI already allows you
  to specify how you want your `input verified`_.
  Contracts, on the other hand, really shine when you want to specify relations
  *between* the endpoints.
* Contracts allow for **automatic test generation**.

  Tools for property-based testing such as `Schemathesis`_ can automatically generate
  test data and verify that your API works as expected.
  Post-conditions are an easy way to define your properties to be tested.

  There is an ongoing discussion with the authors of the Schemathesis how to integrate
  it with tools which generate data based on contracts such as `icontract-hypothesis`_.
* Contracts open up **a wider ecosystem for analysis**.

  When you decorate the endpoints with contracts, you can immediately use analysis
  tools such as `CrossHair`_ to analyze your code and find bugs.

.. _input verified: https://fastapi.tiangolo.com/tutorial/query-params-str-validations/
.. _Schemathesis: https://github.com/schemathesis/schemathesis
.. _icontract-hypothesis: https://github.com/mristin/icontract-hypothesis
.. _CrossHair: https://github.com/pschanely/CrossHair
