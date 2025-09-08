function errorHandler(err, req, res, next) {
  console.error('Unhandled error:', err);
  
  // Errore di validazione
  if (err.name === 'ValidationError') {
    return res.status(400).json({
      error: 'Validation error',
      details: err.message
    });
  }
  
  // Errore di database
  if (err.name === 'PrismaClientKnownRequestError') {
    return res.status(500).json({
      error: 'Database error',
      code: err.code
    });
  }
  
  // Errore generico
  res.status(500).json({
    error: 'Internal server error',
    message: process.env.NODE_ENV === 'development' ? err.message : 'Something went wrong'
  });
}

module.exports = errorHandler;
